from abc import ABC, abstractmethod


class Observer(ABC):
  """Base interface for all notification channels."""

  @abstractmethod
  def update(self, event_data: dict) -> None:
    pass


class EventSubject:
  """Subject that manages subscriptions and triggers events."""

  def __init__(self):
    self._observers: list[Observer] = []

  def subscribe(self, observer: Observer) -> None:
    if observer not in self._observers:
      self._observers.append(observer)

  def unsubscribe(self, observer: Observer) -> None:
    if observer in self._observers:
      self._observers.remove(observer)

  def notify(self, event_data: dict) -> None:
    for observer in self._observers:
      observer.update(event_data)