package booking

type Booking struct {
	Room string
	Hour string
	By   string
}

type Diary struct {
	bookings map[string]Booking
}

func NewDiary() *Diary {
	return &Diary{bookings: map[string]Booking{}}
}

func (d *Diary) Book(room, hour, by string) error {
	d.bookings[room+"@"+hour] = Booking{Room: room, Hour: hour, By: by}
	return nil
}

func (d *Diary) HolderOf(room, hour string) string {
	return d.bookings[room+"@"+hour].By
}
