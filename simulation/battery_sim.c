#include <stdio.h>
#include <stdlib.h>

typedef struct {
    float capacity_mwh;
    float current_charge;
    float efficiency;
    float max_power_mw;
} Battery;

void charge_battery(Battery *b, float energy_available) {
    if (energy_available > b->max_power_mw) {
        energy_available = b->max_power_mw;
    }
    float added_energy = energy_available * b->efficiency;
    b->current_charge += added_energy;
    if (b->current_charge > b->capacity_mwh) {
        b->current_charge = b->capacity_mwh;
    }
    printf("Battery Level: %.2f/%.2f MWh\n", b->current_charge, b->capacity_mwh);
}

int main(int argc, char **argv) {
    Battery my_battery = {10.0, 0.0, 0.9, 2.0};
    printf("--- BATTERY SIMULATION START ---\n");
    charge_battery(&my_battery, 5.0);
    return 0;
}