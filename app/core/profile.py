class Profile:
    def __init__(self, group, profile: dict):
        self.group = group
        self.profile = profile.get('profile', None)
        self.account = profile.get('account', None)
        self.role = profile.get('role', None)
        self.default = profile.get('default', 'false') in ['True', 'true', True]
        self.source = profile.get('source', None)

    def validate(self) -> (bool, str):
        if not self.profile:
            return False, f'a profile in {self.group.name} has no profile'
        if not self.account:
            return False, f'a profile in {self.group.name} has no account'
        if not self.role:
            return False, f'a profile in {self.group.name} has no role'
        return True, ''

    def to_dict(self) -> dict:
        d = {
            'profile': self.profile,
            'account': self.account,
            'role': self.role,
        }
        if self.source:
            d['source'] = self.source
        if self.default:
            d['default'] = True
        return d
