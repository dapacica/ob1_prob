from ob1.agents.qa_agent import QATestingAgent


def main():
    prompt = (
        "Analyze and verify the code from this PR. "
        "If necessary, describe how to run automated tests or correct build issues."
    )

    qa_agent = QATestingAgent()
    qa_agent.run_full_qa_process(prompt)


if __name__ == "__main__":
    main()
