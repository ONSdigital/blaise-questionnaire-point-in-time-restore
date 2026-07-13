def throw_error_if_empty_string(string_input: str, argument_name: str) -> None:
    if not string_input or not string_input.strip():
        raise ValueError(f"{argument_name} cannot be empty or none")
