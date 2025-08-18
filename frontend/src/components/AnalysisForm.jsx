import "../styles/AnalysisForm.css"

const AnalysisForm = ({ persona, setPersona, jobToDo, setJobToDo }) => (
  <div className="card-section">
    <h2>Step 2: Provide Analysis Context</h2>
    <div className="form-group">
      <label htmlFor="persona">Persona</label>
      <input type="text" id="persona" value={persona} onChange={(e) => setPersona(e.target.value)} placeholder="e.g., Financial Analyst, University Researcher" />
    </div>
    <div className="form-group">
      <label htmlFor="job_to_be_done">Job to be Done / Query</label>
      <textarea id="job_to_be_done" value={jobToDo} onChange={(e) => setJobToDo(e.target.value)} rows="3" placeholder="e.g., Identify key risks and future growth opportunities..." />
    </div>
  </div>
);

export default AnalysisForm;