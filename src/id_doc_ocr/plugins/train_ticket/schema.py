from pydantic import BaseModel


class TrainTicketDocument(BaseModel):
    doc_type: str = "train_ticket"
    ticket_number: str | None = None
    passenger_name: str | None = None
    id_number: str | None = None
    train_number: str | None = None
    departure_station: str | None = None
    arrival_station: str | None = None
    departure_time: str | None = None
    seat_no: str | None = None
    fare: str | None = None
