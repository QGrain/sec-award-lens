from secawardlens.awards.sources import (
    parse_ccs_2022,
    parse_ccs_2023,
    parse_ieee_2022,
    parse_ieee_2023,
    parse_ndss_2022,
    parse_ndss_2023,
    parse_usenix_2022,
    parse_usenix_2023,
)


def test_ieee_2022_parser_stops_before_test_of_time_awards() -> None:
    html = """
    <h1 id="distinguished-paper-award">Distinguished Paper Award</h1><hr>
    <p><strong>First Paper</strong>Ada Lovelace (University One)</p>
    <h1 id="test-of-time-award">Test-of-Time Award</h1>
    <p><strong>Old Paper</strong>Alan Turing</p>
    """
    result = parse_ieee_2022(html)
    assert [item.raw_title for item in result] == ["First Paper"]
    assert result[0].authors == ["Ada Lovelace"]


def test_ieee_parser_preserves_raw_provenance() -> None:
    html = """
    <h1 id="distinguished-paper-awards">Awards</h1>
    <div><div class="list-group-item"><b>Paper: A Study</b><br>
    Ada Lovelace (University One), Grace Hopper (University Two)</div></div>
    """
    result = parse_ieee_2023(html)
    assert result[0].raw_title == "Paper: A Study"
    assert result[0].authors == ["Ada Lovelace", "Grace Hopper"]


def test_usenix_parser_ignores_affiliations() -> None:
    html = """
    <article><h2><a href="/paper/example">Paper Title</a></h2>
      <div class="field-name-field-paper-people-text"><p>Ada Lovelace,
      <em>University One;</em> Grace Hopper, <em>University Two</em></p></div>
      <p>Distinguished Paper Award Winner</p>
    </article>
    """
    result = parse_usenix_2023(html)
    assert result[0].authors == ["Ada Lovelace", "Grace Hopper"]
    assert result[0].official_paper_url == "https://www.usenix.org/paper/example"


def test_usenix_2022_parser_uses_the_edition_url() -> None:
    html = """
    <article><h2><a href="/conference/usenixsecurity22/presentation/example">Paper</a></h2>
      <div class="field-name-field-paper-people-text"><p>Ada Lovelace,
      <em>University One</em></p></div><p>Distinguished Paper Award Winner</p></article>
    """
    result = parse_usenix_2022(html)
    assert result[0].official_paper_url.endswith("/usenixsecurity22/presentation/example")


def test_ccs_2022_parser_excludes_honorable_mentions() -> None:
    html = """
    <h2 id="distinguished-paper-award">Distinguished Paper Award</h2>
    <ul><li><strong>Winner</strong><ul><li>Ada Lovelace, Grace Hopper</li></ul></li></ul>
    <h2 id="best-paper-honorable-mention">Honorable Mention</h2>
    <ul><li><strong>Not Included</strong><ul><li>Alan Turing</li></ul></li></ul>
    """
    result = parse_ccs_2022(html)
    assert [item.raw_title for item in result] == ["Winner"]
    assert result[0].authors == ["Ada Lovelace", "Grace Hopper"]


def test_ccs_parser_handles_official_malformed_nested_list() -> None:
    html = """
    <h3>2023</h3><ul><li><b>Ada Lovelace and Grace Hopper</b>, First Paper<br><br>
      <li><b>Alan Turing</b>, Second Paper<br><br></li></li></ul>
    """
    result = parse_ccs_2023(html)
    assert [item.raw_title for item in result] == ["First Paper", "Second Paper"]


def test_ndss_parser_stops_at_next_heading() -> None:
    html = """
    <h3>Distinguished Paper Award Winners</h3>
    <p><a href="https://example.test/paper"><strong>Paper Title</strong></a>
    Ada Lovelace (University One)</p><h3>Next section</h3>
    <p><a href="https://example.test/no"><strong>Not an award</strong></a> Nobody</p>
    """
    result = parse_ndss_2023(html)
    assert len(result) == 1
    assert result[0].raw_title == "Paper Title"


def test_ndss_2022_parser_excludes_poster_awards() -> None:
    html = """
    <h3>2022 Distinguished Paper Award</h3>
    <p><strong><a href="https://example.test/paper">Paper Title</a><br></strong>
    Ada Lovelace (University One)</p>
    <h3>2022 Best Technical Poster Award</h3>
    <p><strong><a href="https://example.test/poster">Poster</a></strong>Nobody</p>
    """
    result = parse_ndss_2022(html)
    assert len(result) == 1
    assert result[0].raw_title == "Paper Title"
    assert result[0].official_paper_url == "https://example.test/paper"
