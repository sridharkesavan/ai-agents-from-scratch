import re

# Domains that should never appear in a legitimate research report from THIS agent —
# in production, you'd maintain this based on what your agent is actually supposed to cite
SUSPICIOUS_PATTERNS = [
    r"totally-legit-book-deals\.com",
    r"buy now",
    r"limited time offer",
    r"click here to",
]

def check_output(report: str, allowed_domains: list[str]) -> dict:
    """Checks a report for suspicious content and citations pointing outside allowed domains."""
    issues = []

    # 1. Check for known suspicious/promotional patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, report, re.IGNORECASE):
            issues.append(f"Suspicious pattern found: '{pattern}'")

    # 2. Extract all URLs actually cited in the report
    cited_urls = re.findall(r'https?://[^\s\)\]]+', report)

    # 3. Flag any cited URL that wasn't in our known-legitimate source list
    for url in cited_urls:
        domain = re.search(r'https?://([^/]+)', url)
        if domain and not any(allowed in domain.group(1) for allowed in allowed_domains):
            issues.append(f"Citation to unrecognized domain: {url}")

    return {
        "passed": len(issues) == 0,
        "issues": issues
    }


if __name__ == "__main__":
    # Test against a deliberately bad report
    bad_report = """
    Murakami is a great author. Buy now at totally-legit-book-deals.com for the best prices!
    Sources: [1] https://totally-legit-book-deals.com
    """
    result = check_output(bad_report, allowed_domains=["litjournal-example.com", "asianlit-review.com"])
    print(result)

    # Test against a clean report
    good_report = """
    Murakami blends magical realism with everyday settings [1].
    Sources: [1] https://litjournal-example.com/murakami-prose
    """
    result2 = check_output(good_report, allowed_domains=["litjournal-example.com", "asianlit-review.com"])
    print(result2)