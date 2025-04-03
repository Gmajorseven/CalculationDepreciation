import datetime
import csv

# Define the Asset class with Carcass Value
class Asset:
    def __init__(self, item_no, item_type, purchase_date, cost, carcass_value, life_years, last_depr_date=None, remaining_amount=None):
        self.item_no = item_no
        self.item_type = item_type
        self.purchase_date = purchase_date
        self.cost = cost
        self.carcass_value = carcass_value  # Used instead of Salvage Value
        self.life_years = life_years
        self.last_depr_date = last_depr_date or purchase_date
        self.remaining_amount = remaining_amount if remaining_amount is not None else cost

    def validate(self):
        if self.item_type != "FA":
            return False, f"Skipping item {self.item_no}: Not a Fixed Asset (FA)."
        if not self.purchase_date:
            return False, f"Error: Missing purchase date for item {self.item_no}."
        return True, None

    def straight_line_depreciation(self):
        """Calculates yearly depreciation using the straight-line method with carcass value."""
        return (self.cost - self.carcass_value) / self.life_years

    def calculate_depreciation(self):
        """Calculates depreciation and returns a report entry."""
        is_valid, message = self.validate()
        if not is_valid:
            return None

        depreciation_per_year = self.straight_line_depreciation()
        current_year = datetime.date.today().year
        start_year = self.last_depr_date.year

        report_data = []
        for year in range(start_year, start_year + self.life_years):
            if self.remaining_amount <= self.carcass_value:
                break

            depreciation_value = min(depreciation_per_year, self.remaining_amount - self.carcass_value)
            self.remaining_amount -= depreciation_value
            self.last_depr_date = datetime.date(year, 12, 31)

            report_data.append([
                self.item_no,
                self.purchase_date,
                self.cost,
                self.carcass_value,
                self.life_years,
                year,
                round(depreciation_value, 2),
                round(self.remaining_amount, 2),
                self.last_depr_date
            ])

        return report_data

# Function to generate the depreciation report with filters
def generate_depreciation_report(assets, filename="depreciation_report.csv", item_no=None, purchase_date_range=None):
    """
    Generates and saves a depreciation report with optional filters.

    Filters:
    - item_no: Only include a specific Item No. (e.g., "A001").
    - purchase_date_range: Tuple (start_date, end_date) to filter by purchase date.
    """
    report_headers = ["Item No", "Purchase Date", "Cost", "Carcass Value", "Life Years", "Year", "Depreciation", "Remaining Amount", "Last Depreciation Date"]
    report_data = []

    for asset in assets:
        # Apply Item No filter
        if item_no and asset.item_no != item_no:
            continue

        # Apply Purchase Date filter
        if purchase_date_range:
            start_date, end_date = purchase_date_range
            if not (start_date <= asset.purchase_date <= end_date):
                continue

        # Calculate depreciation
        data = asset.calculate_depreciation()
        if data:
            report_data.extend(data)

    if not report_data:
        return "No valid depreciation data available."

    # Save report to CSV
    file_path = filename
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(report_headers)
        writer.writerows(report_data)

    return file_path

# Sample Data (Using Carcass Value)
assets = [
    Asset(item_no="A001", item_type="FA", purchase_date=datetime.date(2020, 1, 1), cost=10000, carcass_value=1000, life_years=5),
    Asset(item_no="A002", item_type="EQ", purchase_date=datetime.date(2021, 5, 1), cost=5000, carcass_value=500, life_years=3),
    Asset(item_no="A003", item_type="FA", purchase_date=None, cost=8000, carcass_value=800, life_years=4),
    Asset(item_no="A004", item_type="FA", purchase_date=datetime.date(2022, 3, 15), cost=15000, carcass_value=2000, life_years=6),
]

# Generate filtered depreciation report
filtered_report_path = generate_depreciation_report(assets, filename="filtered_depreciation_report.csv",
                                                    item_no="A004",
                                                    purchase_date_range=(datetime.date(2022, 1, 1), datetime.date(2023, 12, 31)))

print(f"Filtered depreciation report generated: {filtered_report_path}")

