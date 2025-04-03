example_response = {
    # https://platform.openai.com/docs/guides/tools-computer-use#2-receive-a-suggested-action
    "output": [
        {
            "type": "reasoning",
            "id": "rs_67cc...",
            "summary": [
                {
                    "type": "summary_text",
                    "text": "Clicking on the browser address bar."
                }
            ]
        },
        {
            "type": "computer_call",
            "id": "cu_67cc...",
            "call_id": "call_zw3...",
            "action": {
                "type": "click",
                "button": "left",
                "x": 156,
                "y": 50
            },
            "pending_safety_checks": [],
            "status": "completed"
        }
    ]
}
