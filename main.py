from db_utils import add_resident, view_residents, add_parking_slot, view_parking

def show_menu():
    print("\n" + "="*50)
    print("🏠 SOCIETY MANAGEMNT SYSTEM")
    print("="*50)
    print("1.  Add Resident")
    print("2.  View Residents") 
    print("3.  Add Parking Slot")
    print("4.  View Parking Slots")
    print("5.  Maintenance Payments")
    print("6.  Notices")
    print("7.  Complaints")
    print("0.  Exit")
    print("="*50)

def main():
    while True:
        show_menu()
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            name = input("Resident name: ")
            flat = input("Flat number: ")
            phone = input("Phone (optional): ")
            email = input("Email (optional): ")
            family = input("Family members (default 1): ") or "1"
            add_resident(name, flat, phone, email, int(family))
            
        elif choice == '2':
            view_residents()
            
        elif choice == '3':
            slot = input("Parking slot number: ")
            flat = input("Assigned flat (optional): ")
            vehicle = input("Vehicle number (optional): ")
            add_parking_slot(slot, flat or None, vehicle)
            
        elif choice == '4':
            view_parking()
            
        elif choice == '0':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
