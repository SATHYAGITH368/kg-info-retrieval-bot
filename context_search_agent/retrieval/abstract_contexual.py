from abc import ABC,abstractmethod
from typing import Any,List,Dict

class Contexual(ABC):
   

   @abstractmethod
   def parse_query_input(self, **kwargs)->Any:
      pass
   
   @abstractmethod
   def encode_query(self, **kwargs)->Any:
      pass
   
   @abstractmethod
   def perform_retrieval(self, encoded_input: Any,top_k: int=10)->List[Dict[str,Any]]:
      pass
   
   @abstractmethod
   def handle_results(self,results: List[Dict[str,Any]])->None:
      pass
   
   def display_or_store_results(self, **kwargs)->None:
      pass
   
   @abstractmethod
   def search(self, query: str,top_k: int=10)->List[Dict[str,Any]]:
      pass