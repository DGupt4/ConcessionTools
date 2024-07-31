<!-- InputField.svelte -->
<script>
  export let label = "";
  export let id = "";
  export let value = "";
  export let type = "";
  export let min = undefined;
  export let tooltip = "";
</script>

<div class="input-group">
  <label for={id}>
    {label}
    <span class="tooltip-container">
      <svg
        class="question-mark"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        width="16"
        height="16"
      >
        <path
          fill="currentColor"
          d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"
        />
      </svg>

      <span class="tooltip">{tooltip}</span>
    </span>
  </label>

  {#if type === "text"}
    <input type="text" {id} bind:value required {min} />
  {:else if type === "number"}
    <input type="number" {id} bind:value required {min} />
  {:else if type === "datetime-local"}
    <input type="datetime-local" {id} bind:value required {min} />
  {/if}

</div>

<style>
  .input-group {
    margin-bottom: 15px;
  }

  label {
    display: block;
    margin-bottom: 5px;
  }

  input {
    width: 100%;
    padding: 8px;
    background-color: #333;
    border: 1px solid #444;
    color: #ffffff;
  }

  .tooltip-container {
    position: relative;
    display: inline-block;
    margin-left: 5px;
  }

  .question-mark {
    cursor: pointer;
    vertical-align: middle;
  }

  .tooltip {
    visibility: hidden;
    width: 200px;
    background-color: #555;
    color: #fff;
    text-align: center;
    border-radius: 6px;
    padding: 5px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -100px;
    opacity: 0;
    transition: opacity 0.3s;
  }

  .tooltip-container:hover .tooltip {
    visibility: visible;
    opacity: 1;
  }
</style>
