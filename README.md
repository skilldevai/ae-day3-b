# Enterprise AI Accelerator - Day 2 - Part 2

## Model Context Protocol (MCP) ##

These instructions will guide you through configuring a GitHub Codespaces environment that you can use to do the labs. 

<br><br>

**1. Change your codespace's default timeout from 30 minutes to longer (60 suggested).**
To do this, when logged in to GitHub, go to https://github.com/settings/codespaces and scroll down on that page until you see the *Default idle timeout* section. Adjust the value as desired.

![Changing codespace idle timeout value](./images/aia-0-1.png?raw=true "Changing codespace idle timeout value")

**2. Click on the button below to start a new codespace from this repository.**

Click here ➡️  [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/skillrepos/aia-day2-b?quickstart=1)

<br><br>

**3. Then click on the option to create a new codespace.**

![Creating new codespace from button](./images/aia-0-2.png?raw=true "Creating new codespace from button")

This will run for a long time while it gets everything ready.

After the initial startup, it will run a script to setup the python environment and install needed python pieces. This will take several more minutes to run. It will look like this while this is running.

![Final prep](./images/aia-0-5.png?raw=true "Final prep")

The codespace is ready to use when you see a prompt like the one shown below in its terminal.

![Ready to use](./images/aia-0-3.png?raw=true "Ready to use")

<br><br>

**4. Run setup script to finalize the installation.**

In the codespace *TERMINAL* panel at the bottom, run the following command.

```
scripts/setup.sh
```

This will setup the python environment, install needed python pieces, install Ollama, and then download the model we will use. This will take several more minutes to run. 

![Final prep](./images/mcp89.png?raw=true "Final prep")

<br><br>

**5. Open a new terminal.**

When the script is completed (after a long run), you can just click on the "+" sign on the far right to get a new terminal with the provided Python environment to work in.

![New terminal](./images/atoa3.png?raw=true "New terminal")

<br><br>

**6. Open the labs file.**

You can open the [labs.md](./labs.md) file either in your codespace or in a separate browswer tab/instance.**

![Labs](./images/mcp78.png?raw=true "Labs")

<br>

**Now, you are ready for the labs!**

<br><br>



---

## License and Use

These materials are provided as part of the **Enterprise AI Accelerator Workshop** conducted by **TechUpSkills (Brent Laster)**.

Use of this repository is permitted **only for registered workshop participants** for their own personal learning and
practice. Redistribution, republication, or reuse of any part of these materials for teaching, commercial, or derivative
purposes is not allowed without written permission.

© 2025 TechUpSkills / Brent Laster. All rights reserved.




