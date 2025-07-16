class Product:
    """
    Product class to represent a product
    name: str
    description: str
    turnover: str
    launch_date: str
    country: str
    segment: str
    """
    def __init__(self, name: str, description: str, turnover: str, launch_date: str, country: str, segment: str):
        self.name = name
        self.description = description
        self.turnover = turnover
        self.launch_date = launch_date
        self.country = country
        self.segment = segment