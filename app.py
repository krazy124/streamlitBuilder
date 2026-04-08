import streamlit as st
import re
from copy import deepcopy

st.set_page_config(page_title="Streamlit App Builder v3", layout="wide")


# =========================================================
# HELPERS This is a change  
# =========================================================
def make_safe_variable_name(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-zA-Z0-9\s_-]", "", text)
    text = re.sub(r"\s+", "_", text)
    if not text:
        return "my_element"
    if text[0].isdigit():
        text = f"var_{text}"
    return text


def make_safe_class_name(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-zA-Z0-9\s_-]", "", text)
    text = re.sub(r"\s+", "-", text)
    if not text:
        return "my-class"
    if text[0].isdigit():
        text = f"class-{text}"
    return text


def parse_options(options_text: str):
    return [opt.strip() for opt in options_text.split(",") if opt.strip()]


def try_parse_number(value: str):
    try:
        num = float(value)
        if num.is_integer():
            return int(num)
        return num
    except:
        return None


def python_repr(value):
    return repr(value)


def css_value(value: str) -> str:
    return value.strip()


def element_supports_variable(element_type: str) -> bool:
    return element_type not in ["header", "subheader", "write", "markdown", "divider"]


def element_needs_options(element_type: str) -> bool:
    return element_type in ["selectbox", "radio"]


def element_needs_min_max(element_type: str) -> bool:
    return element_type in ["number_input", "slider"]


def build_element_dict(
    element_type: str,
    label: str,
    variable_name: str,
    default_value: str,
    options_text: str,
    min_value: str,
    max_value: str,
    class_name: str
):
    label = label.strip()
    variable_name = variable_name.strip()

    if not variable_name and element_supports_variable(element_type):
        variable_name = make_safe_variable_name(label)

    return {
        "type": element_type,
        "label": label,
        "var": variable_name,
        "default": default_value.strip(),
        "options_text": options_text.strip(),
        "min": min_value.strip(),
        "max": max_value.strip(),
        "class_name": class_name.strip(),
    }


def build_style_class_dict(
    class_name: str,
    color: str,
    background_color: str,
    padding: str,
    margin: str,
    border: str,
    border_radius: str
):
    return {
        "class_name": make_safe_class_name(class_name),
        "color": color.strip(),
        "background_color": background_color.strip(),
        "padding": padding.strip(),
        "margin": margin.strip(),
        "border": border.strip(),
        "border_radius": border_radius.strip(),
    }


def validate_input(element_type: str, label: str):
    if element_type == "divider":
        return True, ""

    if not label.strip():
        return False, "Please enter label/text first."

    return True, ""


def validate_style_class_input(class_name: str):
    if not class_name.strip():
        return False, "Please enter a class name."
    return True, ""


def style_dict_to_css(class_data: dict) -> str:
    class_name = class_data["class_name"]
    lines = [f".{class_name} {{"]

    if class_data["color"]:
        lines.append(f"    color: {css_value(class_data['color'])};")
    if class_data["background_color"]:
        lines.append(f"    background-color: {css_value(class_data['background_color'])};")
    if class_data["padding"]:
        lines.append(f"    padding: {css_value(class_data['padding'])};")
    if class_data["margin"]:
        lines.append(f"    margin: {css_value(class_data['margin'])};")
    if class_data["border"]:
        lines.append(f"    border: {css_value(class_data['border'])};")
    if class_data["border_radius"]:
        lines.append(f"    border-radius: {css_value(class_data['border_radius'])};")

    lines.append("}")
    return "\n".join(lines)


def generate_css_block(style_classes: list[dict]) -> str:
    if not style_classes:
        return ""

    css_parts = []
    for style_class in style_classes:
        css_parts.append(style_dict_to_css(style_class))

    css_joined = "\n\n".join(css_parts)

    return (
        'st.markdown("""\n'
        "<style>\n"
        f"{css_joined}\n"
        "</style>\n"
        '""", unsafe_allow_html=True)'
    )


def build_wrapped_code(inner_code: str, class_name: str) -> list[str]:
    if class_name:
        return [
            f"st.markdown('<div class=\"{class_name}\">', unsafe_allow_html=True)",
            inner_code,
            "st.markdown('</div>', unsafe_allow_html=True)",
        ]
    return [inner_code]


def element_to_code_lines(el: dict) -> list[str]:
    element_type = el["type"]
    label = el["label"]
    variable_name = el["var"]
    default_value = el["default"]
    options_text = el["options_text"]
    min_value = el["min"]
    max_value = el["max"]
    class_name = el["class_name"]

    label_code = python_repr(label)

    if element_type == "text_input":
        if default_value:
            inner = f'{variable_name} = st.text_input({label_code}, value={python_repr(default_value)})'
        else:
            inner = f"{variable_name} = st.text_input({label_code})"
        return build_wrapped_code(inner, class_name)

    if element_type == "text_area":
        if default_value:
            inner = f'{variable_name} = st.text_area({label_code}, value={python_repr(default_value)})'
        else:
            inner = f"{variable_name} = st.text_area({label_code})"
        return build_wrapped_code(inner, class_name)

    if element_type == "number_input":
        args = [label_code]

        min_num = try_parse_number(min_value)
        max_num = try_parse_number(max_value)
        default_num = try_parse_number(default_value)

        if min_num is not None:
            args.append(f"min_value={min_num}")
        if max_num is not None:
            args.append(f"max_value={max_num}")
        if default_num is not None:
            args.append(f"value={default_num}")

        inner = f"{variable_name} = st.number_input({', '.join(args)})"
        return build_wrapped_code(inner, class_name)

    if element_type == "slider":
        min_num = try_parse_number(min_value)
        max_num = try_parse_number(max_value)
        default_num = try_parse_number(default_value)

        if min_num is None:
            min_num = 0
        if max_num is None:
            max_num = 100
        if default_num is None:
            default_num = min_num

        inner = (
            f"{variable_name} = st.slider("
            f"{label_code}, min_value={int(min_num)}, max_value={int(max_num)}, value={int(default_num)})"
        )
        return build_wrapped_code(inner, class_name)

    if element_type == "selectbox":
        options = parse_options(options_text)
        if not options:
            options = ["Option 1", "Option 2"]
        inner = f"{variable_name} = st.selectbox({label_code}, {python_repr(options)})"
        return build_wrapped_code(inner, class_name)

    if element_type == "radio":
        options = parse_options(options_text)
        if not options:
            options = ["Option 1", "Option 2"]
        inner = f"{variable_name} = st.radio({label_code}, {python_repr(options)})"
        return build_wrapped_code(inner, class_name)

    if element_type == "checkbox":
        default_bool = default_value.lower() in ["true", "yes", "1", "checked"]
        inner = f"{variable_name} = st.checkbox({label_code}, value={default_bool})"
        return build_wrapped_code(inner, class_name)

    if element_type == "button":
        inner = f"{variable_name} = st.button({label_code})"
        return build_wrapped_code(inner, class_name)

    if element_type == "header":
        inner = f"st.header({label_code})"
        return build_wrapped_code(inner, class_name)

    if element_type == "subheader":
        inner = f"st.subheader({label_code})"
        return build_wrapped_code(inner, class_name)

    if element_type == "write":
        inner = f"st.write({label_code})"
        return build_wrapped_code(inner, class_name)

    if element_type == "markdown":
        inner = f"st.markdown({label_code})"
        return build_wrapped_code(inner, class_name)

    if element_type == "divider":
        inner = "st.divider()"
        return build_wrapped_code(inner, class_name)

    return [f"# Unsupported element type: {element_type}"]


def generate_full_code(elements: list[dict], style_classes: list[dict]) -> str:
    lines = [
        "import streamlit as st",
        "",
        'st.set_page_config(page_title="My Streamlit App", layout="wide")',
        "",
    ]

    css_block = generate_css_block(style_classes)
    if css_block:
        lines.append("# --- Generated CSS ---")
        lines.append(css_block)
        lines.append("")

    lines.append("# --- Generated UI ---")

    if not elements:
        lines.append('st.write("Your generated app is empty so far.")')
    else:
        for el in elements:
            lines.extend(element_to_code_lines(el))

    return "\n".join(lines)


def pretty_element_summary(el: dict) -> str:
    t = el["type"]
    label = el["label"] or "(no label)"
    var = el["var"]
    class_name = el["class_name"] or "None"

    if element_supports_variable(t):
        return f"{t} | label='{label}' | var='{var}' | class='{class_name}'"
    return f"{t} | text='{label}' | class='{class_name}'"


def compact_style_summary(style_class: dict) -> str:
    parts = []
    if style_class["color"]:
        parts.append(f"color: {style_class['color']}")
    if style_class["background_color"]:
        parts.append(f"bg: {style_class['background_color']}")
    if style_class["padding"]:
        parts.append(f"padding: {style_class['padding']}")
    if style_class["margin"]:
        parts.append(f"margin: {style_class['margin']}")
    if style_class["border"]:
        parts.append(f"border: {style_class['border']}")
    if style_class["border_radius"]:
        parts.append(f"radius: {style_class['border_radius']}")

    if not parts:
        return "No styles set."

    return " | ".join(parts)


def render_preview_wrapper_start(class_name: str):
    if class_name:
        st.markdown(f'<div class="{class_name}">', unsafe_allow_html=True)


def render_preview_wrapper_end(class_name: str):
    if class_name:
        st.markdown("</div>", unsafe_allow_html=True)


def render_preview_css(style_classes: list[dict]):
    if not style_classes:
        return

    css_lines = ["<style>"]
    for style_class in style_classes:
        css_lines.append(style_dict_to_css(style_class))
        css_lines.append("")
    css_lines.append("</style>")

    st.markdown("\n".join(css_lines), unsafe_allow_html=True)


def render_preview_element(el: dict, index: int):
    element_type = el["type"]
    label = el["label"]
    default_value = el["default"]
    options_text = el["options_text"]
    min_value = el["min"]
    max_value = el["max"]
    class_name = el["class_name"]

    preview_key = f"preview_{index}_{el['type']}_{el['var']}_{class_name}"

    render_preview_wrapper_start(class_name)

    if element_type == "text_input":
        st.text_input(label, value=default_value, key=preview_key)

    elif element_type == "text_area":
        st.text_area(label, value=default_value, key=preview_key)

    elif element_type == "number_input":
        min_num = try_parse_number(min_value)
        max_num = try_parse_number(max_value)
        default_num = try_parse_number(default_value)

        kwargs = {"label": label, "key": preview_key}
        if min_num is not None:
            kwargs["min_value"] = min_num
        if max_num is not None:
            kwargs["max_value"] = max_num
        if default_num is not None:
            kwargs["value"] = default_num

        st.number_input(**kwargs)

    elif element_type == "slider":
        min_num = try_parse_number(min_value)
        max_num = try_parse_number(max_value)
        default_num = try_parse_number(default_value)

        if min_num is None:
            min_num = 0
        if max_num is None:
            max_num = 100
        if default_num is None:
            default_num = min_num

        st.slider(
            label,
            min_value=int(min_num),
            max_value=int(max_num),
            value=int(default_num),
            key=preview_key
        )

    elif element_type == "selectbox":
        options = parse_options(options_text)
        if not options:
            options = ["Option 1", "Option 2"]
        st.selectbox(label, options, key=preview_key)

    elif element_type == "radio":
        options = parse_options(options_text)
        if not options:
            options = ["Option 1", "Option 2"]
        st.radio(label, options, key=preview_key)

    elif element_type == "checkbox":
        default_bool = default_value.lower() in ["true", "yes", "1", "checked"]
        st.checkbox(label, value=default_bool, key=preview_key)

    elif element_type == "button":
        st.button(label, key=preview_key)

    elif element_type == "header":
        st.header(label)

    elif element_type == "subheader":
        st.subheader(label)

    elif element_type == "write":
        st.write(label)

    elif element_type == "markdown":
        st.markdown(label)

    elif element_type == "divider":
        st.divider()

    render_preview_wrapper_end(class_name)


def load_style_class_into_form(style_class: dict):
    st.session_state.style_class_name = style_class["class_name"]
    st.session_state.style_color = style_class["color"]
    st.session_state.style_background_color = style_class["background_color"]
    st.session_state.style_padding = style_class["padding"]
    st.session_state.style_margin = style_class["margin"]
    st.session_state.style_border = style_class["border"]
    st.session_state.style_border_radius = style_class["border_radius"]


# =========================================================
# SESSION STATE
# =========================================================
if "elements" not in st.session_state:
    st.session_state.elements = []

if "style_classes" not in st.session_state:
    st.session_state.style_classes = []

if "generated_code" not in st.session_state:
    st.session_state.generated_code = generate_full_code(
        st.session_state.elements,
        st.session_state.style_classes
    )

if "style_class_name" not in st.session_state:
    st.session_state.style_class_name = ""

if "style_color" not in st.session_state:
    st.session_state.style_color = ""

if "style_background_color" not in st.session_state:
    st.session_state.style_background_color = ""

if "style_padding" not in st.session_state:
    st.session_state.style_padding = ""

if "style_margin" not in st.session_state:
    st.session_state.style_margin = ""

if "style_border" not in st.session_state:
    st.session_state.style_border = ""

if "style_border_radius" not in st.session_state:
    st.session_state.style_border_radius = ""


# =========================================================
# TITLE
# =========================================================
st.title("Streamlit App Builder v3")
st.caption("Build elements, define reusable style classes, and generate a starter Streamlit app.")


# =========================================================
# TABS
# =========================================================
tab_elements, tab_styles = st.tabs(["Elements", "Style Classes"])


# =========================================================
# ELEMENTS TAB
# =========================================================
with tab_elements:
    element_types = [
        "text_input",
        "text_area",
        "number_input",
        "slider",
        "selectbox",
        "radio",
        "checkbox",
        "button",
        "header",
        "subheader",
        "write",
        "markdown",
        "divider",
    ]

    class_options = [""] + [style_class["class_name"] for style_class in st.session_state.style_classes]
    class_labels = ["None"] + [style_class["class_name"] for style_class in st.session_state.style_classes]

    with st.form("add_element_form", clear_on_submit=True):
        top_left, top_right = st.columns([1, 2])

        with top_left:
            form_element_type = st.selectbox("Element Type", element_types, index=0)

        with top_right:
            form_label = st.text_input(
                "Label / Text",
                placeholder="Example: Name"
            )

        suggested_var = make_safe_variable_name(form_label)
        selected_type = form_element_type

        mid1, mid2 = st.columns(2)

        with mid1:
            disabled_var = not element_supports_variable(selected_type)
            form_var = st.text_input(
                "Variable Name",
                placeholder=f"Suggested: {suggested_var}",
                disabled=disabled_var
            )

        with mid2:
            selected_class_label = st.selectbox("Style Class", class_labels, index=0)
            form_class_name = "" if selected_class_label == "None" else selected_class_label

        low1, low2 = st.columns(2)

        with low1:
            form_default = st.text_input(
                "Default Value",
                placeholder="Optional default value"
            )

        with low2:
            st.text_input(
                "Class Preview",
                value=form_class_name if form_class_name else "None",
                disabled=True
            )

        form_options = ""
        form_min = ""
        form_max = ""

        if element_needs_options(selected_type):
            form_options = st.text_input(
                "Options (comma-separated)",
                placeholder="Example: Red, Blue, Green"
            )

        if element_needs_min_max(selected_type):
            mm1, mm2 = st.columns(2)
            with mm1:
                form_min = st.text_input("Min Value", placeholder="Example: 0")
            with mm2:
                form_max = st.text_input("Max Value", placeholder="Example: 100")

        add_submitted = st.form_submit_button("Add Element", use_container_width=True)

    if add_submitted:
        is_valid, msg = validate_input(form_element_type, form_label)
        if not is_valid:
            st.warning(msg)
        else:
            new_el = build_element_dict(
                element_type=form_element_type,
                label=form_label,
                variable_name=form_var,
                default_value=form_default,
                options_text=form_options,
                min_value=form_min,
                max_value=form_max,
                class_name=form_class_name
            )
            st.session_state.elements.append(new_el)
            st.session_state.generated_code = generate_full_code(
                st.session_state.elements,
                st.session_state.style_classes
            )
            st.rerun()

    e1, e2, e3 = st.columns(3)

    with e1:
        if st.button("Delete Last", use_container_width=True, key="elements_delete_last"):
            if st.session_state.elements:
                st.session_state.elements.pop()
                st.session_state.generated_code = generate_full_code(
                    st.session_state.elements,
                    st.session_state.style_classes
                )
                st.rerun()

    with e2:
        if st.button("Clear All Elements", use_container_width=True, key="elements_clear_all"):
            st.session_state.elements = []
            st.session_state.generated_code = generate_full_code(
                st.session_state.elements,
                st.session_state.style_classes
            )
            st.rerun()

    with e3:
        st.download_button(
            "Download app.py",
            data=st.session_state.generated_code,
            file_name="app.py",
            mime="text/x-python",
            use_container_width=True,
            key="download_app_py"
        )

    st.divider()

    left_col, right_col = st.columns([1.15, 1])

    with left_col:
        st.subheader("Elements")

        if not st.session_state.elements:
            st.info("No elements added yet.")
        else:
            for i, el in enumerate(st.session_state.elements):
                row1, row2 = st.columns([6, 1])

                with row1:
                    st.code(pretty_element_summary(el), language="text")

                with row2:
                    if st.button("✕", key=f"remove_element_{i}", use_container_width=True):
                        st.session_state.elements.pop(i)
                        st.session_state.generated_code = generate_full_code(
                            st.session_state.elements,
                            st.session_state.style_classes
                        )
                        st.rerun()

        st.subheader("Generated Code")

        edited_code = st.text_area(
            "Code Editor",
            value=st.session_state.generated_code,
            height=500,
            key="generated_code_editor"
        )

        if edited_code != st.session_state.generated_code:
            st.session_state.generated_code = edited_code

    with right_col:
        st.subheader("Live Preview")

        preview_elements = deepcopy(st.session_state.elements)

        if not preview_elements:
            st.info("Your preview will appear here after you add elements.")
        else:
            preview_box = st.container(border=True)
            with preview_box:
                render_preview_css(st.session_state.style_classes)
                for i, el in enumerate(preview_elements):
                    render_preview_element(el, i)


# =========================================================
# STYLE CLASSES TAB
# =========================================================
with tab_styles:
    with st.form("style_class_form", clear_on_submit=False):
        top1, top2 = st.columns(2)

        with top1:
            form_style_class_name = st.text_input(
                "Class Name",
                key="style_class_name",
                placeholder="Example: card-primary"
            )

        with top2:
            suggested_class = make_safe_class_name(form_style_class_name)
            st.text_input(
                "Safe Class Name Preview",
                value=suggested_class,
                disabled=True
            )

        row1, row2 = st.columns(2)
        with row1:
            form_style_color = st.text_input(
                "Text Color",
                key="style_color",
                placeholder="Example: #222222"
            )
        with row2:
            form_style_background_color = st.text_input(
                "Background Color",
                key="style_background_color",
                placeholder="Example: #f5f5f5"
            )

        row3, row4 = st.columns(2)
        with row3:
            form_style_padding = st.text_input(
                "Padding",
                key="style_padding",
                placeholder="Example: 12px"
            )
        with row4:
            form_style_margin = st.text_input(
                "Margin",
                key="style_margin",
                placeholder="Example: 8px 0"
            )

        row5, row6 = st.columns(2)
        with row5:
            form_style_border = st.text_input(
                "Border",
                key="style_border",
                placeholder="Example: 1px solid #cccccc"
            )
        with row6:
            form_style_border_radius = st.text_input(
                "Border Radius",
                key="style_border_radius",
                placeholder="Example: 8px"
            )

        s1, s2 = st.columns(2)

        with s1:
            save_class_submitted = st.form_submit_button("Save Class", use_container_width=True)

        with s2:
            clear_class_form_submitted = st.form_submit_button("Clear Form", use_container_width=True)

    if clear_class_form_submitted:
        st.session_state.style_class_name = ""
        st.session_state.style_color = ""
        st.session_state.style_background_color = ""
        st.session_state.style_padding = ""
        st.session_state.style_margin = ""
        st.session_state.style_border = ""
        st.session_state.style_border_radius = ""
        st.rerun()

    if save_class_submitted:
        is_valid, msg = validate_style_class_input(form_style_class_name)
        if not is_valid:
            st.warning(msg)
        else:
            new_class = build_style_class_dict(
                class_name=form_style_class_name,
                color=form_style_color,
                background_color=form_style_background_color,
                padding=form_style_padding,
                margin=form_style_margin,
                border=form_style_border,
                border_radius=form_style_border_radius
            )

            existing_index = None
            for i, existing in enumerate(st.session_state.style_classes):
                if existing["class_name"] == new_class["class_name"]:
                    existing_index = i
                    break

            if existing_index is not None:
                st.session_state.style_classes[existing_index] = new_class
            else:
                st.session_state.style_classes.append(new_class)

            st.session_state.generated_code = generate_full_code(
                st.session_state.elements,
                st.session_state.style_classes
            )
            st.rerun()

    st.divider()

    st.subheader("Saved Style Classes")

    if not st.session_state.style_classes:
        st.info("No style classes saved yet.")
    else:
        for i, style_class in enumerate(st.session_state.style_classes):
            c1, c2, c3 = st.columns([5, 1, 1])

            with c1:
                st.code(
                    f"{style_class['class_name']} | {compact_style_summary(style_class)}",
                    language="text"
                )

            with c2:
                if st.button("Edit", key=f"edit_style_class_{i}", use_container_width=True):
                    load_style_class_into_form(style_class)
                    st.rerun()

            with c3:
                if st.button("✕", key=f"delete_style_class_{i}", use_container_width=True):
                    deleted_class_name = st.session_state.style_classes[i]["class_name"]
                    st.session_state.style_classes.pop(i)

                    for element in st.session_state.elements:
                        if element["class_name"] == deleted_class_name:
                            element["class_name"] = ""

                    st.session_state.generated_code = generate_full_code(
                        st.session_state.elements,
                        st.session_state.style_classes
                    )
                    st.rerun()

    st.divider()

    st.subheader("Generated CSS Preview")

    if not st.session_state.style_classes:
        st.info("No CSS generated yet.")
    else:
        css_preview_lines = []
        for style_class in st.session_state.style_classes:
            css_preview_lines.append(style_dict_to_css(style_class))
            css_preview_lines.append("")

        st.code("\n".join(css_preview_lines), language="css")
