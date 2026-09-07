package pallet

import "time"

// Pallet is one physical pallet in a warehouse aisle.
type Pallet struct {
	LicencePlate string
	Aisle        string
	ReceivedAt   time.Time
}
