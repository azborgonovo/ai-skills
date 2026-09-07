package booking

import "testing"

func TestHolderOfIsEmptyForAFreeRoom(t *testing.T) {
	diary := NewDiary()

	if holder := diary.HolderOf("Blue", "10:00"); holder != "" {
		t.Fatalf("holder = %q, want an empty string", holder)
	}
}
