class DatabaseQueryChecker:
    """
    Class to check the validity of database queries.
    """

    def __init__(self, query):
        self.query = query

    def check(self) -> dict:
        """
        Performs basic validation of the SQL query string.
        Returns a natural language evaluation.
        """
        self.query = self.query.strip()
        if not self.query:
            return "Query is empty."

        allowed_keywords = ["select", "with"]
        dml_keywords = ["insert", "update", "delete"]
        first_word = self.query.lower().split()[0]
        if first_word in dml_keywords:
            output = f"Execution of DML queries ('{first_word.upper()}') is not allowed."
            return {"message": output}

        if first_word not in allowed_keywords:
            output = f"Query starts with '{first_word}', which is not allowed. Use SELECT, or WITH."
            return {"message": output}

        if ";" in self.query:
            output = "Avoid using semicolons (;) in agent-submitted queries."
            return {"message": output}
        
        output = "Query appears syntactically valid. Ready to execute."
        return {"message": output}