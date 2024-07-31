<script>
  import InputField from "../components/InputField.svelte";
  import { onMount } from "svelte";

  let job = {
    group_name: "",
    game_date: "",
    sheet_url: "",
    sheet_num: "",
    num_ppl: "",
    wait_time: "",
  };

  let jobStatus = "";
  let jobTime = 0;
  let interval;

  onMount(() => {
    updateStatus();
    interval = setInterval(updateStatus, 1000);
  });

  async function updateStatus() {
    const response = await fetch("api/job_status", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    const result = await response.json();
    jobStatus = result.status;
    if (jobStatus === 'waiting time') {
      countdown()
    }
  }

  async function countdown() {
  }

  async function startJob() {
    const response = await fetch("api/start_process", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(job),
    });
    const result = await response.json();
    alert(`Job started with ID: ${result.job_id}`);
  }

  async function terminateJob() {
    const response = await fetch("api/terminate_job", {
      method: "POST",
    });
    const result = await response.json();
    alert(result.message);
  }
</script>

<main>
  <header>
    <h1>Concession Picker</h1>
  </header>

  <section class="status-section">
    <div class="status-container">
      <p>
        <b>Job Status: </b><span id="job-status" class={jobStatus.toLowerCase()}
          >{jobStatus}</span
        >
      </p>
      <p><b>Remaining Time: </b>{jobTime}</p>
    </div>
  </section>

  <form on:submit|preventDefault={startJob}>
    <InputField
      label="Group Name"
      id="group-name"
      bind:value={job.group_name}
      tooltip="Enter the desired GroupMe group name i.e. 1/11/23 Michigan Concessions"
      type="text"
    />

    <InputField
      label="Game Date"
      id="game-date"
      bind:value={job.game_date}
      tooltip="Enter the game date and time"
      type="datetime-local"
    />

    <InputField
      label="Sheet URL"
      id="sheet-url"
      bind:value={job.sheet_url}
      tooltip="Enter the google spreadsheet url"
      type="text"
    />

    <InputField
      label="Sheet Number"
      id="sheet-number"
      bind:value={job.sheet_num}
      tooltip="Enter the sheet number where the responses are stored"
      type="number"
    />

    <InputField
      label="Number of People"
      id="num-ppl"
      bind:value={job.num_ppl}
      tooltip="Enter the desired people to work at the concession"
      type="number"
      min="1"
    />

    <InputField
      label="Wait Time"
      id="wait-time"
      bind:value={job.wait_time}
      tooltip="Enter the time to wait in minutes"
      type="number"
      min="1"
    />
    <button type="submit">Submit</button>
  </form>

  <button id="terminate-button" on:click={terminateJob}>Terminate</button>
</main>

<style>
  :global(body) {
    background-color: #1a1a1a;
    color: #ffffff;
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
  }

  main {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
  }

  header {
    background-color: #2c2c2c;
    padding: 20px;
    margin-bottom: 20px;
  }

  h1 {
    margin: 0;
  }

  button {
    background-color: #4a4a4a;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    cursor: pointer;
    transition: background-color 0.3s;
  }

  button:hover {
    background-color: #5a5a5a;
  }

  #terminate-button {
    margin-top: 10px;
    background-color: #ff4444;
  }

  #terminate-button:hover {
    background-color: #ff6666;
  }

  .status-section {
    background-color: #2c2c2c;
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 5px;
  }

  .status-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .status-container p {
    margin: 0;
    font-size: 1em;
  }

  .idle {
    color: #888;
  }

  .completed {
    color: #4caf50;
  }

  .terminated {
    color: #f44336;
  }

  .job-status {
    color: #2196f3;
  }
</style>
