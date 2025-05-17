README.md

The two scripts work together to keep our shipping-rate logic both accurate and easy to use.
 update_shipping_schedule.py ingests raw order data (with actual package weights and paid delivery costs), 
 bins each shipment into the predefined weight brackets, and recalculates the average charge 
 for each bracket—then spits out a clean CSV that becomes our “master” shipping schedule. 
 shipping_lookup.py uses that master file to power a simple lookup tool: enter any SKU 
 and it returns the current estimated shipping cost based on the item’s weight. By separating the 
 data-refresh process (recomputing real-world averages) from the lookup logic, we ensure our pricing 
 tays up-to-date with how much we really pay to ship, avoid under- or over-charging customers, 
 and give both operations and customer-service teams an easy, reliable way to quote or audit shipping fees.


 Run with python3 update_shipping_schedule.py