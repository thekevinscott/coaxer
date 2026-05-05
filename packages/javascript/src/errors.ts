export class MissingVariableError extends Error {
  constructor(variable: string) {
    super(`Missing required variable: ${variable}`);
    this.name = "MissingVariableError";
  }
}
