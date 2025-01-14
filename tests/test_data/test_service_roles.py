def get_test_service_roles() -> dict:
    return {
        "team-1": {
            "selected_profile": "profile-1",
            "selected_role": "role-1",
            "available": {
                "profile-1": [
                    "role-1-1",
                    "role-1-2"
                ],
                "profile-2": [
                    "role-2-1",
                    "role-2-2"
                ],
                "profile-3": [
                    "role-3-1",
                    "role-3-2"
                ]
            },
            "history": [
                "profile-2 : role-2",
                "profile-1 : role-3",
                "profile-4 : role-4",
                "profile-3 : role-1",
            ]
        },
        "team-2": {
            "selected_profile": "profile-2",
            "selected_role": "role-3",
            "available": {},
            "history": [
                "profile-2 : role-3",
            ]
        }
    }

