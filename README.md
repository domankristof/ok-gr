# "OK GR"
Your personal AI-powered coach that draws on your race data to offer tailored insight, custom teaching points and summaries/logs of data to help you reach the podium. 

## 1. High Level Overview
### 1.1 The Problem
* Most amateur GR-Cup teams lack a dedicated race engineer to analyse data or provide structured coaching.

* After conducting my research into typical team workflows, I found how under-utilised telemetry and lap data are at this level.

### 1.2 The Solution - OK-GR
* OK-GR makes racing data digestible and actionable for drivers without deep technical backgrounds and for teams without dedicated race engineers.

* It transforms raw CSVs into clear insights, helping amateur teams become more competitive and making the series more accessible.

* The concept is to have a highly personalisable dashboard, with the GR-Agent focusing entirely on where you are struggling the most.

### 1.3 How this Helps the Drivers of the GR-Cup
* Gives small teams the ability to leverage thier data, as if they had a professional race engineer.

* Provides structured driver coaching and actionable feedback, making all teams more competitve.

* Makes the series more appealing to skilled drivers without large technical teams.

## 2. How it Works
### 2.1 Static Data Summaries
OK-GR currently provides the following visual summaries during a coaching session:

1. **Speed-Distance Plots** - Compares the average of your mid-race pace laps with your fastest lap to highlight where time is gained or lost.

2. **Race Session Timing Metrics** - Displays PB lap, finishing position, race fastest lap, and delta to the session’s fastest lap.

3. **Weather Condition Metrics** - Shows averaged air/track temperature, wind speed, humidity, and rain events.

4. **G-G Plot & Traction Margins** - Displays lateral vs longitudinal acceleration with an estimated traction ellipse and two reference G-circles to show remaining grip margin.

4. **Sector Timing Metrics** - Shows PB sector times, deltas to the fastest driver, and optimal-lap comparison.

### 2.2 Interactive AI Race Engineer
A chat interface on the right side of the screen gives you access to your AI race engineer. You can ask questions, request analysis, and receive coaching in natural language.

## 3. Current Functional Capabilties of Your Race Engineer
Due to the limited time I had to prototype, GR-Agent currently has only a couple of tools at its disposal (through function calling) to analyse and coach you on your race data. Your race engineer can assist you with:

1. **Telemetry Analysis**
    * Steering smoothness score
    * Micro-correction detection
    * Steering usage overview

2. **Lap, Delta & Sector Analysis**
    * Sector-by-sector coaching and comparison to leaders
    * Optimal-lap calculation and placement estimates
    * Identification of biggest performance gains + actionable guidancedriving.

3. **Creation of a Downloadable Coaching Summart Document**
      * Coaching summary with actionable insights into improving driving.


## 4. How to Use OK-GR
1. Download the files from this link: click here

2. Open the app and go to the upload section.

3. Select your vehicle number and the correct telemetry session.

4. Upload each file into its respective field (e.g., Top 10 Laps File, Weather File).

5. Press Submit to start the analysis session.

6. Review your static summaries and chat with your AI race engineer.

7. Ask GR-Agent to generate a downloadable coaching summary.


## 5. Important Notes
1.  Please use dark-mode on your device/browser for best UI apperance.

2. Some telemetry sessions lack GPS or acceleration channels, please choose a data session containing both to avoid errors.

## 6. What Next For OK-GR
1. Integrate voice-to-speech coaching to allow hands-free interaction.

2. Share the tool with GR-Cup drivers for real-world testing and see how we can itterate on OK-GR.

3. I would like to also explore integrating OK-GR into consumer GR cars as a track-day training assistant. The car would pull together telemetry data during your session outing, and between sessions you can debrief with GR-Agent and they will coach you on how you can improve, based on your fresh data. Conversing through natural language.
