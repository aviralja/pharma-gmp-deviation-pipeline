from files.agents import summarizerAgent
#! executive-level GMP deviation summary from QA
def summary_qa(input_data) -> str:
    query = f"""Take a set of raw Q/A pairs from a GMP deviation report section and generate 
    a clear, professional summary. The summary must: 
    1. Retain compliance and regulatory language.
    2. Be concise but comprehensive enough for expert brainstorming.
    3. Highlight critical details (root causes, corrective actions, CAPA links, SOP references).
    4. Use an executive-level narrative style suitable for pharma experts.
    5. Avoid repetition or copying raw Q/A text directly.
    Here are the Q/A pairs:
    Q/A: {input_data}
    """
    result = summarizerAgent.kickoff(query)
    return result.raw
