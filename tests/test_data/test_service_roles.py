def get_test_service_roles() -> dict:
    return {
        "development": {
            "selected_profile": "developer",
            "selected_role": "pipeline",
            "available": {
                "profile-1": [
                    "role-1-1",
                    "role-1-2"
                ],
                "profile-2": [
                    "role-2-1"
                ],
            },
            "history": [
                "profile-2 : role-2",
                "profile-1 : role-3",
            ]
        },
        "live": {
            "selected_profile": None,
            "selected_role": None,
            "available": {},
            "history": []
        }
    }
