from app.ingest import chunk_text, _detect_section_priority, _md_sections

def test_chunk_text_with_overlap():
    text = "one two three four five six seven eight"
    chunks = chunk_text(text, chunk_size=3, overlap=1)
    assert chunks == [
        "one two three",
        "three four five",
        "five six seven",
        "seven eight",
    ]

def test_detect_section_priority_high():
    """Test that high-priority sections are correctly identified"""
    high_priority_sections = [
        "SLA",
        "Policy",
        "Terms and Conditions",
        "Refund Policy",
        "Warranty Policy",
        "Compliance Notes",
    ]
    for section in high_priority_sections:
        assert _detect_section_priority(section) == "high", f"Expected 'high' for '{section}'"

def test_detect_section_priority_medium():
    """Test that medium-priority sections are correctly identified"""
    medium_priority_sections = [
        "Agent Guide",
        "Product Catalog",
        "Exclusions",
        "Cut-off Times",
        "Shipping Information",
        "Delivery & Shipping",  # Note: "Delivery Policy" would be high (contains "policy")
    ]
    for section in medium_priority_sections:
        assert _detect_section_priority(section) == "medium", f"Expected 'medium' for '{section}'"

def test_detect_section_priority_low():
    """Test that low-priority sections are correctly identified"""
    low_priority_sections = [
        "Introduction",
        "Body",
        "Notes",
        "Miscellaneous",
        "",
    ]
    for section in low_priority_sections:
        assert _detect_section_priority(section) == "low", f"Expected 'low' for '{section}'"

def test_md_sections_detects_heading_levels():
    """Test that _md_sections correctly detects heading levels"""
    text = """# H1 Title
        Content under H1
        ## H2 Title
        Content under H2
        ### H3 Title
        Content under H3
        #### H4 Title
        Content under H4
    """
    sections = _md_sections(text)
    assert len(sections) == 4
    assert sections[0][0] == "H1 Title"
    assert sections[0][2] == 1  # heading_level
    assert sections[1][0] == "H2 Title"
    assert sections[1][2] == 2  # heading_level
    assert sections[2][0] == "H3 Title"
    assert sections[2][2] == 3  # heading_level
    assert sections[3][0] == "H4 Title"
    assert sections[3][2] == 4  # heading_level

def test_md_sections_handles_body_without_heading():
    """Test that sections without headings get heading_level=0"""
    text = "Just some text without a heading"
    sections = _md_sections(text)
    assert len(sections) == 1
    assert sections[0][0] == "Body"
    assert sections[0][2] == 0  # heading_level