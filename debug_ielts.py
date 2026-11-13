
"""Test whether Eduling's IELTS information can be retrieved."""

from backend.knowledge_base import records, approved
from backend.retrieval import search

question = "What IELTS speaking courses does Eduling offer?"

# Check both FAQ and course knowledge bases.
collections = {
    "faq": "faqs.json",
    "course": "courses.json",
}

for kind, filename in collections.items():

    # Load all records from the JSON file.
    all_records = records(filename)

    print(f"\n--- {kind.upper()} ---")

    # Check whether IELTS information exists and is approved.
    for record in all_records:
        if "ielts" in str(record).lower():
            print("IELTS record:", record.get("id"))
            print("Status:", record.get("status"))
            print("Approved:", approved(record))

    # Filter to approved information only.
    approved_records = [
        record for record in all_records
        if approved(record)
    ]

    # Retrieve matches, including low-scoring ones.
    results = search(
        question,
        approved_records,
        kind=kind,
        limit=5,
        min_score=0.0,
    )

    print("\nRetrieval results:")
    for result in results:
        print(result)
