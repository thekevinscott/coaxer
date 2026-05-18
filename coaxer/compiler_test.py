import json
from pathlib import Path

import pytest

from coaxer.compiler import _parse_json_object, distill

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "__fixtures__" / "labels" / "demo"


def describe_distill():
    def it_writes_all_artifacts(tmp_path: Path):
        out = tmp_path / "prompt_out"
        distill(FIXTURE, out, optimizer=None)
        assert (out / "prompt.jinja").is_file()
        assert (out / "meta.json").is_file()
        assert (out / "history.jsonl").is_file()

    def it_records_compile_info_in_meta_json(tmp_path: Path):
        out = tmp_path / "prompt_out"
        distill(FIXTURE, out, optimizer=None)
        meta = json.loads((out / "meta.json").read_text())
        assert meta["example_count"] == 3
        assert "compiled_at" in meta
        assert "label_hash" in meta
        assert "fields" in meta
        assert set(meta["fields"]["inputs"]) == {"readme", "description", "stars"}

    def it_appends_history_jsonl_on_recompile(tmp_path: Path):
        out = tmp_path / "prompt_out"
        distill(FIXTURE, out, optimizer=None)
        distill(FIXTURE, out, optimizer=None)
        lines = (out / "history.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            entry = json.loads(line)
            assert "compiled_at" in entry

    def it_raises_on_unknown_optimizer(tmp_path: Path):
        out = tmp_path / "prompt_out"
        with pytest.raises(ValueError, match="optimizer"):
            distill(FIXTURE, out, optimizer="nonesuch")

    def describe_template():
        @pytest.mark.parametrize("slot", ["{{ readme }}", "{{ description }}", "{{ stars }}"])
        def it_has_input_slot(tmp_path: Path, slot: str):
            out = tmp_path / "prompt_out"
            distill(FIXTURE, out, optimizer=None)
            template = (out / "prompt.jinja").read_text()
            assert slot in template

        def it_is_valid_jinja(tmp_path: Path):
            from coaxer.prompt import CoaxedPrompt

            out = tmp_path / "prompt_out"
            distill(FIXTURE, out, optimizer=None)
            p = CoaxedPrompt(out)
            filled = p(readme="# hi", description="demo", stars=42)
            assert "# hi" in filled
            assert "42" in filled

        def it_has_no_double_period(tmp_path: Path):
            out = tmp_path / "prompt_out"
            distill(FIXTURE, out, optimizer=None)
            template = (out / "prompt.jinja").read_text()
            assert ".." not in template

        def it_has_single_inputs_and_field_descriptions_block(tmp_path: Path):
            # The template owns the `Inputs:` heading; instructions should use
            # `Field descriptions:` instead so there's exactly one of each.
            out = tmp_path / "prompt_out"
            distill(FIXTURE, out, optimizer=None)
            template = (out / "prompt.jinja").read_text()
            assert template.count("Inputs:") == 1
            assert template.count("Field descriptions:") == 1

        def it_surfaces_enum_allowed_values(tmp_path: Path):
            # Demo fixture's output is an enum of ["true", "false"].
            out = tmp_path / "prompt_out"
            distill(FIXTURE, out, optimizer=None)
            template = (out / "prompt.jinja").read_text()
            assert "Respond with exactly one of:" in template
            assert "true" in template
            assert "false" in template

    def describe_output_name():
        def it_defaults_to_output_in_meta(tmp_path: Path):
            out = tmp_path / "prompt_out"
            distill(FIXTURE, out, optimizer=None)
            meta = json.loads((out / "meta.json").read_text())
            assert meta["output_name"] == "output"

        def it_persists_a_custom_output_name(tmp_path: Path):
            out = tmp_path / "prompt_out"
            distill(FIXTURE, out, optimizer=None, output_name="is_curated")
            meta = json.loads((out / "meta.json").read_text())
            assert meta["output_name"] == "is_curated"


def describe_parse_json_object():
    def it_returns_none_for_non_string_values():
        # The GEPA metric reads gold/pred via ``getattr(..., None)``; when the
        # field is missing on the prediction, the value is ``None`` and must
        # short-circuit to the exact-match fallback rather than blow up.
        assert _parse_json_object(None) is None
        assert _parse_json_object(42) is None

    def it_returns_none_for_invalid_json():
        # Malformed JSON must fall through to exact match, not propagate the
        # decode error and crash the GEPA optimization loop.
        assert _parse_json_object("{not json") is None

    def it_returns_none_for_non_object_json():
        # ``json.loads("true")`` succeeds and yields a bool; only dicts get
        # the per-key semantic scoring, everything else falls through.
        assert _parse_json_object("true") is None
        assert _parse_json_object("[1, 2, 3]") is None

    def it_returns_parsed_dict_for_json_objects():
        assert _parse_json_object('{"a": 1}') == {"a": 1}
