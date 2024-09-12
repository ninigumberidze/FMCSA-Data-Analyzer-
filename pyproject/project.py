"""ეს პროექტი არის აპლიკაცია სახელწოდებით FMCSA Data Analyzer,
ის შექმნილია საავტომობილო გადამზიდავ კომპანიებთან დაკავშირებული მონაცემების მართვის, დამუშავების,
ანალიზისა და ვიზუალიზაციისთვის. პროექტი აგებულია პითონის გამოყენებით და უზრუნველყოფს 
მონაცემთა ჩატვირთვას, დამუშავებას, ვიზუალიზაციას და გაგებას. პროექტის ინსპირაცია კი თანდართული 
სხვადასხვა ტიპის მონაცემთა ბაზის ფაილები გახდა"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from threading import Thread
import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DatabaseManager:
    """DatabaseManager ეს კლასი ამუშავებს მონაცემთა ბაზის ისეთ ოპერაციებს როგორიცაა ცხრილების შექმნა,
 მონაცემების ჩასმა და მონაცემების შერჩევა SQLite მონაცემთა ბაზიდან(fmcsa_data.db). 
 ის უზრუნველყოფს მონაცემთა ბაზის ცხრილის fmcsa_data შექმნას 
 თუ ის არ არსებობს და საშუალებას აძლევს მონაცემთა ჩასმას და მოძიებას pandas DataFrames-ის გამოყენებით
    ატრიბუტები:db_name (str): ]SQLite database file-ის სახელი.
    """

    def __init__(self, db_name: str):
        self.db_name = db_name

    def create_table(self) -> None:
        """იქმნება fmcsa_data table მისი არ არსებობის შემთხვევაშ."""
        try:
            create_table_query: str = """
            CREATE TABLE IF NOT EXISTS fmcsa_data (
            company_name VARCHAR(50) NOT NULL,
            address VARCHAR(50) NOT NULL,
            drivers INT NOT NULL,
            vehicles INT NOT NULL,
            commodities_carried VARCHAR(50) NOT NULL
            );
            """
            with sqlite3.connect(self.db_name) as conn:
                conn.execute(create_table_query)
            print("Table created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def insert_data(self, data: pd.DataFrame) -> None:
        """
        მონაცემების ჩატვირთვა fmcsa_data ცხრილში.
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                data.to_sql('fmcsa_data', conn, if_exists='append', index=False)
            print("Data inserted successfully.")
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")

    def select_data(self) -> pd.DataFrame:
        """
  იღებს ყველა მონაცემს ცხრილიდან და აბრუნებს მათ (pd.DataFrame)
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                return pd.read_sql_query("SELECT * FROM fmcsa_data", conn)
        except sqlite3.Error as e:
            print(f"Error selecting data: {e}")
            return pd.DataFrame()

class DataProcessor(DatabaseManager):
    """
    კლასი რათა დაამუშაოს და გაანალიზოს მონაცემები რომელიც მემკვიდერობითაა გადაცემული DatabaseManager კლასიდან
    ატრიბუტი:data (pd.DataFrame)
    """

    def __init__(self, db_name: str):
        super().__init__(db_name)
        self.data = None

    def load_data_from_csv(self, file_name: str) -> None:
        """
       csv ფაილიდან იღებს მოანაცემებს პანდას გამოყენებით.
        """
        try:
            print(f"Loading data from CSV: {file_name}")
            self.data = pd.read_csv(file_name)
            print("Data loaded successfully.")
            self.create_table()
            print("Table created or already exists.")
            self.insert_data(self.data)
            print("Data inserted into database.")
        except Exception as e:
            print(f"Error loading data from CSV: {e}")

    def process_data(self) -> None:
        """აანალიზებს ჩამოტვირთულ მონაცემებს."""
        if self.data is None:
            self.data = self.select_data()

        self.data['drivers_per_vehicle'] = self.data['drivers'] / self.data['vehicles']
        print("Data processed successfully.")

    def visualize_data(self) -> plt.Figure:
        """
        დამუშავებული მონაცემების ვიზუალიზაცია.
        """
        try:
            if self.data is None:
                print("Data is None, fetching from database.")
                self.data = self.select_data()
            else:
                print("Using existing data for visualization.")
            
            print("Processing data...")
            self.data['drivers_per_vehicle'] = self.data['drivers'] / self.data['vehicles']

            print("Generating visualization...")
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            #დიაგრამა რომელიც გვიჩვენებს საშუალოდ მძღოლებს ყველა მანქანაზე პროდუქტის მიხედვით
            avg_drivers_per_vehicle = self.data.groupby('commodities_carried')['drivers_per_vehicle'].mean().sort_values(ascending=False)
            ax1.bar(avg_drivers_per_vehicle.index, avg_drivers_per_vehicle.values)
            ax1.set_title('Average Drivers per Vehicle by Commodity')
            ax1.set_xlabel('Commodity')
            ax1.set_ylabel('Avg Drivers per Vehicle')
            ax1.tick_params(axis='x', rotation=45)

            # მანქანები მძღოლების მიხედვით
            ax2.scatter(self.data['vehicles'], self.data['drivers'])
            ax2.set_title('Drivers vs Vehicles')
            ax2.set_xlabel('Number of Vehicles')
            ax2.set_ylabel('Number of Drivers')

            plt.tight_layout()
            print("Visualization created successfully.")
            return fig

        except Exception as e:
            print(f"Error in visualize_data: {e}")

class GUI:
    """ეს კლასი ქმნის ინტერფეისს Tkinter-ის გამოყენებით. ის უზრუნველყოფს ღილაკებს
      CSV ფაილებიდან მონაცემების ჩატვირთვის, მონაცემების ჩვენებისა და მონაცემების ვიზუალიზაციისთვის."""

    def __init__(self, master):
        self.master = master
        self.master.title("FMCSA Data Analyzer")
        self.processor = DataProcessor("fmcsa_data.db")

        self.load_button = ttk.Button(master, text="Load CSV", command=self.load_data)
        self.load_button.pack(pady=10)

        self.display_button = ttk.Button(master, text="Display Data", command=self.display_data)
        self.display_button.pack(pady=10)

        self.visualize_button = ttk.Button(master, text="Visualize Data", command=self.show_visualization)
        self.visualize_button.pack(pady=10)

        self.text_area = tk.Text(master, height=10, width=50)
        self.text_area.pack(pady=10)

    def load_data(self):
        """ტვირთვს მონაცემებს ფაილიდან და სვამს ბაზაში."""
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            print(f"Selected CSV file: {file_path}")
            thread = Thread(target=self._load_data_thread, args=(file_path,))
            thread.start()

    def _load_data_thread(self, file_path):
        """Thread ფუნქცია მონაცემთა ჩატვირთვისთვის."""
        try:
            print("Loading data in thread...")
            self.processor.load_data_from_csv(file_path)
            print("Data loaded and inserted into database.")
            self.master.after(0, lambda: self.text_area.insert(tk.END, "Data loaded successfully.\n"))
        except Exception as e:
            print(f"Error loading data in thread: {e}")

    def display_data(self):
        """GUIში აჩვენებს მონაცემებს ბაზიდან."""
        data = self.processor.select_data()
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, data.to_string())
        print("Data displayed.")

    def show_visualization(self):
        """GUIში აჩვენებს მონაცემების ვიზუალიზაციას."""
        try:
            print("Generating visualization...")
            fig = self.processor.visualize_data()
            top = tk.Toplevel(self.master)
            canvas = FigureCanvasTkAgg(fig, master=top)
            canvas.draw()
            canvas.get_tk_widget().pack()
            print("Visualization displayed.")
        except Exception as e:
            print(f"Error showing visualization: {e}")
#მეინ ფუნქცია ძირითადი ფუნქციების გამოძახებისთვის
def main():
    print("Starting FMCSA Data Analyzer...")
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
