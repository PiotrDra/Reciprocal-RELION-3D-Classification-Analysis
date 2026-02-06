import pandas as pd
from pySankey.sankey import sankey
import matplotlib.pyplot as plt

df = pd.read_csv('RP1_vs_RP2_pysenkey_input.csv', sep=',')

# Ensure weight (in this case .#particles) is numeric (just in case)
df['#particles'] = pd.to_numeric(df['#particles'], errors='coerce')

#make sankey graph
sankey(
    left=df["RP1_class"],
    right=df["RP2_class"],
    leftWeight=df["#particles"],
    rightWeight=df["#particles"],
    aspect=20,
    fontsize=20
)

# Get current figure
fig = plt.gcf()
# Set size in inches

fig.set_size_inches(6, 6)

# Set the color of the background to white
fig.set_facecolor("w")

# Save the figure
fig.savefig("customers-goods.png", bbox_inches="tight", dpi=150)

