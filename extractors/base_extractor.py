from abc import ABC, abstractmethod
class BaseExtractor(ABC):
    """
    Clase abstracta para los extractores. 
    """

    @abstractmethod
    def extract(self) -> list[dict]:
        """
        Extrae ofertas de empleo de la fuente correspondiente. 
        Devuelve lista de diccionarios con los datos crudos normalizads de cada oferta
        """
        pass