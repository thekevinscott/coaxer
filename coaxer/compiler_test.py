import json
from pathlib import Path

import pytest

from coaxer.compiler import distill

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
