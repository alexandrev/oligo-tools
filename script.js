function resetInput() {
  document.getElementById('sequenceInput').value = '';
  document.getElementById('buildingblock_container').innerHTML = '';
  document.getElementById('responsive_area').innerHTML = `
  This tool can calculate various molecular parameters of PNAs, peptides as well as PNA-peptide-conjugates. For the calculation enter the full sequece (separated by spaces) including N- or C-Terminal modifications. Base monomers are all amino acids in single or three letter code (single letters: Caps, three letter code: First letter in upper case, subsequent letters in lower case). <br /> <b>Note:</b> Building blocks with wrong capitalization like "gly" or "lYs" will not be recognized. To avoid reporting wrong numbers unkown building blocks are replaced by building block "UKN" which has such high values that this should not stay unnoticed.<br/>
  <ul>
  <li><b>Modifications at the N-Terminus</b><br />
  Modifications at the N-Terminus can simply be added as "first" building block, like "<b><i>FAM</i></b> K C D K G CONH2" or "<b><i>TAMRA</i></b> R C K N N CONH2"</li>
  <li><b>Modifications at the C-Terminus</b><br />
  Modifications at the C-Terminus can simply be added as "last" building block, like "K C D K G <b><i>COOH</i></b> " or "R C K N N <b><i>CONH2</i></b>"<br/>
  <b>Note:</b> While it is not necessary to explicitly declare a free N-Terminus it is necessary to add "COOH" as group to denote a free C-terminus!</li>
  <li><b>Internal Modifications</b><br />
  Internal modifications can be added to a building block in round brackets
  like "Lys(<b><i>FAM</i></b>) K C D K G COOH" or "Lys(<b><i>TAMRA</i></b>) R C K N N COOH"</li>
  <li><b>Special Modifications</b><br />
  Besides typical fluorophores it is possible to use "p" to indicate a phosphorylation (e.g. "p Tyr") and a tilde at a Cystein residue to indicate a disulfide bond (e.g. "Ac C(~) K G N R C(~) COOH")</li>
  </ul>
  A full list of building blocks will be provided at the "/building_blocks" API-endpoint which is currently still work in progress.
  `;
}

function calculate() {
  const sequence = document.getElementById('sequenceInput').value;
  if (sequence.trim() === '') {
    alert('Please enter a sequence.');
    return;
  }

  const resultDiv = document.getElementById('responsive_area');
  //resultDiv.innerHTML = `<div aria-busy="true">Calculating...</div>`
  resultDiv.innerHTML = `<progress></progress>`;

  // Make GET request to the API (same origin as the served page).
  // encodeURIComponent prevents special characters in the sequence from
  // breaking the query string.
  const apiUrl = `/calc/all_features?sequence=${encodeURIComponent(sequence)}`;
  fetch(apiUrl)
    .then(response => response.json())
    .then(data => {
      displayResult(data);
    })
    .catch(error => {
      console.error('Error fetching data:', error);
      alert('Error fetching data. Please retry in a moment.');
    });
}

function buildingBlocks() {
  bbdiv = document.getElementById('buildingblock_container');
  const blocks = bbdiv.innerHTML;
  if (blocks.trim() === '') {
    console.log("FooBar");
    bbdiv.innerHTML = `<progress></progress>`;
    const apiUrl = `/building_blocks`;
    fetch(apiUrl)
      .then(response => response.json())
      .then(data => {
        bbdiv.innerHTML = `
        <br/>
        <h4>Building Blocks</h4>
        <b>Amino Acids</b><br /> ${data.AminoAcids}<br />
        <b>PNA monomers</b><br /> ${data.PNAmonomers}<br />
        <b>Protecting Groups</b><br /> ${data.ProtectingGroups}<br />
        <b>Fluorophores</b><br /> ${data.Fluorophores}<br />
        <b>C-terminal Modifications</b><br /> ${data.CTerminalModifications}<br />
        `;
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        alert('Error fetching data. Please retry in a moment.');
      });
    return;
  }
  bbdiv.innerHTML='';
}

// TODO: Add termination sequences to result
function displayResult(data) {
  const resultDiv = document.getElementById('responsive_area');
  resultDiv.innerHTML = `
    <h4>Results:</h4>
    <b>Molecular Weight:</b> ${data.MolWt}<br />
    <b>Exact Mass:</b> ${data.Exact}<br />
    <b>Molecular Formula:</b> ${createMolecularFormula(data['Mol Formula'])}<br />
    <b>HPLC-SIM Ions:</b> ${createSIMIonList(data['HPLC-SIM Ions'])}<br />
    <b>MolWt Ions:</b> ${createIonList(data['MolWt Ions'])}<br />
    <b>HRMS Ions:</b> ${createIonList(data['HRMS Ions'])}<br /><br />
  `;
}

function createMolecularFormula(obj) {
  let formula = '';
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      if (obj[key] > 0) {
        formula += `${key}<sub>${obj[key]}</sub>`;
      }
    }
  }
  return formula;
}

function createSIMIonList(obj) {
  let ions = '';
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
        ions += `${obj[key]}; `;
    }
  }
  return ions;
}

function createIonList(obj) {
  let ions = '';
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
        ions += `[M+${key}H]<sup>${key}+</sup>: ${obj[key]}; `;
    }
  }
  return ions;
}