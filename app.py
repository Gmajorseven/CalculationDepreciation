from flask import Flask, render_template, request, send_file, redirect, url_for
import datetime
import csv
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Define the Asset class with Carcass Value
class Asset:
    def __init__(self, item_no, item_type, purchase_date, cost, carcass_value, life_years, last_depr_date=None, remaining_amount=None):
        self.item_no = item_no
        self.item_type = item_type
        self.purchase_date = purchase_date
        self.cost = cost
        self.carcass_value = carcass_value
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
    report_headers = ["Item No", "Purchase Date", "Cost", "Carcass Value", "Life Years", "Year", "Depreciation", "Remaining Amount", "Last Depreciation Date"]
    report_data = []

    for asset in assets:
        print(f"Processing: {asset.item_no}, Purchase Date: {asset.purchase_date}")  # Debugging

        # ✅ Fix: Only filter by item_no if it's provided and non-empty
        if item_no and item_no.strip():
            print(f"Filtering by Item No: {item_no.strip()}")
            if asset.item_no.strip().lower() != item_no.strip().lower():  
                print(f"Skipping {asset.item_no}: Doesn't match item filter ({item_no})")
                continue

        # ✅ Keep date filtering logic unchanged
        if purchase_date_range:
            start_date, end_date = purchase_date_range
            if start_date and asset.purchase_date < start_date:
                print(f"Skipping {asset.item_no}: Purchased before {start_date}")
                continue
            if end_date and asset.purchase_date > end_date:
                print(f"Skipping {asset.item_no}: Purchased after {end_date}")
                continue

        # Perform depreciation calculation
        data = asset.calculate_depreciation()
        if data:
            report_data.extend(data)

    if not report_data:
        return "No valid depreciation data available."

    # Save report to current folder
    file_path = os.path.join("static", filename)
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(report_headers)
        writer.writerows(report_data)

    return file_path


@app.route("/", methods=["GET", "POST"])
def index():
    error_message = None  # Store error messages
    
    if request.method == "POST":
        item_no = request.form.get("item_no")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        print(f"DEBUG: Received Filters -> Item No: {item_no}, Start Date: {start_date}, End Date: {end_date}")  # Debugging

        # Convert dates from strings
        try:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        except ValueError:
            return "Error: Invalid date format. Use YYYY-MM-DD."

        print(f"DEBUG: Parsed Dates -> Start: {start_date}, End: {end_date}")  # Debugging

        # Read uploaded file
        file = request.files["asset_file"]
        if file and file.filename.endswith(".csv"):
            file_path = os.path.join("static", file.filename)
            file.save(file_path)
            
            assets = []
            with open(file_path, "r") as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    try:
                        item_no_csv, item_type, purchase_date, cost, carcass_value, life_years = row
                        
                        # ✅ Debug before filtering
                        print(f"DEBUG: Read Asset -> {item_no_csv}, Type: {item_type}, Date: {purchase_date}")

                        # Validate empty purchase date
                        if not purchase_date.strip():
                            error_message = f"Error: Missing purchase date for item {item_no_csv}."
                            return render_template("index.html", error_message=error_message)

                        purchase_date = datetime.datetime.strptime(purchase_date, "%Y-%m-%d").date()
                        
                        # ✅ Only process FA assets
                        if item_type.strip() != "FA":
                            print(f"Skipping {item_no_csv}: Not an FA item")
                            continue
                        
                        assets.append(Asset(item_no_csv, item_type, purchase_date, float(cost), float(carcass_value), int(life_years)))

                    except Exception as e:
                        return f"Error processing file: {str(e)}"
            
            print(f"DEBUG: Total FA assets for processing: {len(assets)}")  # Debugging
            
            # Generate report
            report_path = generate_depreciation_report(assets, filename="depreciation_report.csv", 
                                                       item_no=item_no, purchase_date_range=(start_date, end_date))

            return redirect(url_for("download", filename="depreciation_report.csv"))

        else:
            error_message = "Invalid file format. Please upload a CSV file."

    return render_template("index.html", error_message=error_message)

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join("static", filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

