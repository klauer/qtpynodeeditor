class Serializable:
    def save(self) -> dict:
        """
        save

        Returns
        -------
        value : QJsonObject
        """
        ...

    def restore(self, q_json_object: dict):
        """
        restore

        Parameters
        ----------
        q_json_object : QJsonObject
        """
        ...
