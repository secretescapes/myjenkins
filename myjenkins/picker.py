from .util import PrettyRepr

ANY = (2 ** 32) - 1 # HACK


class Picker(PrettyRepr):
    """Picks out values from visited nodes."""

    def __init__(self, pick_only=ANY):
        self.pick_only = pick_only
        self.found_on = None
        self.found_value = None

    def evaluate(self, build):
        if not self.has_match:
            picked = self.pick(build)
            matches = self.pick_only == ANY or picked == self.pick_only

            if picked is not None and matches:
                self.found_on = build
                self.found_value = picked

    def pick(self, build):
        raise NotImplementedError()

    @property
    def has_match(self):
        return self.found_on is not None


class Branch(Picker):
    """Picks out job branches."""

    def pick(self, build):
        return build.get_params().get('BRANCH_NAME') or build._get_git_rev_branch()[0]['name']


class Revision(Picker):
    """Picks out build revision."""

    def pick(self, build):
        try:
            return build.get_revision()
        except KeyError:
            return build._get_git_rev()
