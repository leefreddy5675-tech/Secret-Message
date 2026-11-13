rom dataclasses import dataclass
import random
from drafter import (
    route,
    start_server,
    set_site_information,
    Page,
    Text,
    Button,
    TextBox,
    SelectBox,
    CheckBox,
    LineBreak,
    Div,
)
from bakery import assert_equal

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
MAX_MESSAGE_LENGTH = 20


@dataclass
class GridRow:
    """Represents a single row in the generated word search puzzle"""
    row_number: int
    letters: str


@dataclass
class State:
    """Tracks the user's secret message, settings, and current grid rows"""
    current_message: str
    grid_size: int
    uppercase_only: bool
    grid_rows: list[GridRow]


def clean_message(raw_text: str) -> str:
    """Strips outer whitespace and removes spaces from the secret message."""
    return raw_text.strip().replace(" ", "")


def build_word_search_rows(message: str, size: int, uppercase: bool) -> list[GridRow]:
    """
    Creates a list of GridRow objects hiding the message horizontally.
    Note: Uses randomness, so exact output varies on each run.
    """
    letters = ALPHABET.upper() if uppercase else ALPHABET
    formatted_msg = message.upper() if uppercase else message.lower()

    actual_size = max(size, len(formatted_msg) + 2)
    target_row = random.randint(0, actual_size - 1)
    max_start_col = actual_size - len(formatted_msg)
    start_col = random.randint(0, max_start_col)

    rows: list[GridRow] = []
    for row_idx in range(actual_size):
        row_chars: list[str] = []
        for col_idx in range(actual_size):
            if (
                row_idx == target_row
                and start_col <= col_idx < start_col + len(formatted_msg)
            ):
                msg_index = col_idx - start_col
                row_chars.append(formatted_msg[msg_index])
            else:
                row_chars.append(random.choice(letters))
        rows.append(GridRow(row_number=row_idx + 1, letters=" ".join(row_chars)))
    return rows


@route
def index(state: State) -> Page:
    """Home page where the user enters a secret message and grid options."""
    return Page(
        state,
        [
            Text("Secret Message Word Search"),
            Text("Enter a secret message (1 to 20 characters):"),
            TextBox("user_text", state.current_message),
            LineBreak(),
            Text("Choose Grid Size:"),
            SelectBox("selected_size", ["8", "10", "12"], str(state.grid_size)),
            LineBreak(),
            CheckBox("use_uppercase", state.uppercase_only),
            Text("Hide message in ALL CAPS"),
            LineBreak(),
            Button("Enter", check_message),
        ],
    )


@route
def check_message(
    state: State, user_text: str, selected_size: str, use_uppercase: bool
) -> Page:
    """Validates message length and routes to error or confirmation pages."""
    cleaned = clean_message(user_text)
    state.current_message = cleaned
    state.grid_size = int(selected_size)
    state.uppercase_only = use_uppercase

    if len(cleaned) == 0:
        return empty_error(state)
    elif len(cleaned) > MAX_MESSAGE_LENGTH:
        return too_long_error(state)
    else:
        return confirm_message(state)


@route
def empty_error(state: State) -> Page:
    """Error page shown when the user submits an empty text box."""
    return Page(
        state,
        [
            Text("Looks like nothing was typed!"),
            Text("Please go back and enter at least 1 letter."),
            Button("Back", back_to_start),
        ],
    )


@route
def too_long_error(state: State) -> Page:
    """Error page shown when the message exceeds 20 characters."""
    return Page(
        state,
        [
            Text("That message is too long!"),
            Text(
                f"Your message had {len(state.current_message)} characters. "
                f"Keep it under {MAX_MESSAGE_LENGTH} characters."
            ),
            Button("Back", back_to_start),
        ],
    )


@route
def confirm_message(state: State) -> Page:
    """Confirmation page asking the user to verify their secret message."""
    return Page(
        state,
        [
            Text("Your secret message is:"),
            Text(f'"{state.current_message}"'),
            Text("Is that right?"),
            Button("Yes", reveal_hidden),
            Button("No", deny_message),
        ],
    )


@route
def deny_message(state: State) -> Page:
    """Resets the current message if the user clicks No on confirmation."""
    state.current_message = ""
    return index(state)


@route
def reveal_hidden(state: State) -> Page:
    """
    Generates the word search grid in State and displays each GridRow.
    Note: Contains random letter generation, so exact output cannot be unit tested.
    """
    state.grid_rows = build_word_search_rows(
        state.current_message, state.grid_size, state.uppercase_only
    )

    page_items = [
        Text("Hidden Message Word Search"),
        Text("Can you spot your secret message in the grid below?"),
    ]
    for row in state.grid_rows:
        page_items.append(Div(Text(row.letters)))

    page_items.append(LineBreak())
    page_items.append(Button("Back", back_to_start))
    return Page(state, page_items)


@route
def back_to_start(state: State) -> Page:
    """Clears the active grid and message, then returns to the home page."""
    state.current_message = ""
    state.grid_rows = []
    return index(state)


set_site_information(
    author="Freddy Lee",
    description="A website that hides secret messages inside a random word search.",
    sources=["Drafter Documentation"],
    planning=["plan.pdf"],
    links=[],
)

# --- Unit Tests ---
assert_equal(clean_message("  hello world  "), "helloworld")
assert_equal(clean_message("   "), "")

# Test empty message routing
assert_equal(
    check_message(State("", 10, False, []), "   ", "10", False),
    empty_error(State("", 10, False, [])),
)

# Test message too long routing
long_msg = "abcdefghijklmnopqrstuvwxyz"
assert_equal(
    check_message(State("", 10, False, []), long_msg, "10", False),
    too_long_error(State(long_msg, 10, False, [])),
)

# Test valid message routing
assert_equal(
    check_message(State("", 10, True, []), "secret", "10", True),
    confirm_message(State("secret", 10, True, [])),
)

# Test deny_message and back_to_start routes
assert_equal(
    deny_message(State("secret", 10, True, [])),
    index(State("", 10, True, [])),
)
sample_rows = [GridRow(1, "a b c"), GridRow(2, "d e f")]
assert_equal(
    back_to_start(State("secret", 10, True, sample_rows)),
    index(State("", 10, True, [])),
)

start_server(State("", 10, True, []))

