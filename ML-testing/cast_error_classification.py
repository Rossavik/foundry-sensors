import pandas as pd

# Assume data has already been loaded with the 'vrakårsak' column
def load_data():
    # Dummy data loading function
    data = pd.read_csv('cast_error_data.csv')
    return data
    

def main():
    data = load_data()
    vrakårsak_values = data['vrakårsak'].unique()
    change_cast_error = []

    for i, vrakårsak in enumerate(vrakårsak_values):
        print(f"{i+1}. vrakårsak: {vrakårsak}")
        user_input = input("Set 'cast error' to false? (y/n): ").strip().lower()
        if user_input == 'y':
            change_cast_error.append(vrakårsak)
    
    # Saving the results
    with open('vrakårsak_cast_error_changes.txt', 'w') as file:
        for item in change_cast_error:
            file.write(f"{item}\n")
    
    print("List of 'vrakårsak' with 'cast error' set to false saved to 'vrakårsak_cast_error_changes.txt'.")

if __name__ == "__main__":
    main()
