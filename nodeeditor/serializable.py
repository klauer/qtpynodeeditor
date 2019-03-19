class Serializable:
    def save(self) -> dict:
        """
        Save

        Returns
        -------
        value : QJsonObject
        """
        ...

    def restore(self, q_json_object: dict):
        """
        Restore

        Parameters
        ----------
        q_json_object : QJsonObject
        """
        ...
