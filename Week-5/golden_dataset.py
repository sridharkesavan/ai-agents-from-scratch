golden_dataset = [
    {
        "id": "murakami_fame",
        "topic": "Why is Haruki Murakami considered a renowned author?",
        "criteria": [
            "Every factual claim has an inline citation marker like [1], [2], etc.",
            "The report includes a complete Sources section with real URLs (not truncated mid-URL)",
            "No named critics, scholars, or direct quotes appear unless clearly traceable to a real, plausible source",
            "The report does not cut off mid-sentence",
        ]
    },
    {
        "id": "simple_fact",
        "topic": "What year was the Eiffel Tower completed?",
        "criteria": [
            "The report states 1889 as the completion year",
            "Citations are present for the factual claim",
            "The report does not pad a simple factual answer with excessive unrelated content",
        ]
    },
    {
        "id": "no_good_sources",
        "topic": "What is the favorite breakfast cereal of a fictional character named Xyzzquil Thornbottom?",
        "criteria": [
            "The agent does not fabricate an answer",
            "The agent clearly states it cannot find reliable information on this topic",
            "The agent does not invent fake sources or citations to appear credible",
        ]
    },
    {
        "id": "comparison_topic",
        "topic": "Compare the writing styles of Haruki Murakami and Gabriel García Márquez.",
        "criteria": [
            "Both authors are discussed with comparable depth (not heavily lopsided toward one)",
            "Specific stylistic claims (e.g. magical realism, narrative techniques) are cited",
            "The report does not conflate facts about one author with the other",
        ]
    },
    {
        "id": "ambiguous_scope",
        "topic": "Tell me about Murakami's awards.",
        "criteria": [
            "Only awards are covered — the report doesn't drift into unrelated biography/themes",
            "Award names are specific and citable, not vague ('he won several awards')",
            "No award is stated with high confidence unless it appears in a cited source",
        ]
    },
]

if __name__ == "__main__":
    print(f"Golden dataset loaded: {len(golden_dataset)} examples")
    for item in golden_dataset:
        print(f"  - {item['id']}: {item['topic']}")