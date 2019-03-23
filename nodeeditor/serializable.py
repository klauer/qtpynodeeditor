class Serializable:
    def save(self) -> dict:
        """
        Save

        Returns
        -------
        value : dict
        """
        ...

    def restore(self, state: dict):
        """
        Restore

        Parameters
        ----------
        state : dict
        """
        ...
