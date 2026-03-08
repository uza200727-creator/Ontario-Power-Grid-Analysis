#include <stdio.h>
#include <stdlib.h>
// Create a battery structure with values of capacity, current charge, effiency, and max power allowed
typedef struct {
    float capacity_mwh;
    float current_charge;
    float efficiency;
    float max_power_mw;
} Battery;
//Batery charging function
void charge_battery(Battery *b, float energy_available) {
    //If energy used to charge is more than max power, limit it to max power
    if (energy_available > b->max_power_mw) {
        energy_available = b->max_power_mw;
    }
    //Added energy is the energy available multiplied by efficiency of the battery
    float added_energy = energy_available * b->efficiency;
    // Add the energy to the current charge, but if it exceeds capacity, set it to capacity
    b->current_charge += added_energy;
    if (b->current_charge > b->capacity_mwh) {
        b->current_charge = b->capacity_mwh;
    }
    printf("Battery level: %.2f/%.2f MWh\n", b->current_charge, b->capacity_mwh);
}

int main(int argc, char **argv) {
    //Create a battery with 10 MWh capacity, 0 MWh current charge, 90% efficiency, and max power of 2 MW
    Battery my_battery = {10.0, 0.0, 0.9, 2.0};
    printf("Battery smulation:\n");
    //Run the battery charging function with 5 MW of energy available
    charge_battery(&my_battery, 5.0);
    return 0;
}