const API_URL = "https://www.superheroapi.com/api.php/580896453900662"; 
 
const userInput = document.getElementById("userInput"); 
const userSearch = document.getElementById("userSearch"); 
const randomSearch = document.getElementById("randomSearch"); 
const output = document.getElementById("output"); 
 
userSearch.addEventListener("click", async function () { 
 
  const hero_name = userInput.value; 
 
  if (hero_name === "") { 
    output.textContent = "Please enter a SuperHero name."; 
    return; 
  } 
 
  output.innerHTML = ` <div class="loading-container"> 
                      <div class="loading-spinner"></div> 
                      </div>`; 
 
  try { 
    const response = await fetch(`${API_URL}/search/${hero_name}`); 
 
    if (!response.ok) { 
      throw new Error("Network response not ok"); 
    } 
 
    const json = await response.json(); 
    const hero = json.results[0]; 
 
    output.innerHTML = ` 
    <div class ="heroContainer" > 
    <img class ="heroImg" src = ${hero.image.url}> 
    <div class = "heroStats"> 
        <h2 class = "heroName" >${hero.name}</h2> 
        ${Object.keys(hero.powerstats) 
          .map( 
            (stat) => ` 
            <div class="stat"> 
                <span class="statEmoji">${statsToEmoji[stat]}</span> 
                <span class="statName">${stat.toUpperCase()}:</span> 
                <span class="statValue">${hero.powerstats[stat]}</span> 
            </div> 
        ` 
          ) 
          .join("")} 
    </div> 
  </div> 
        `; 
  } catch (error) { 
    output.textContent = "Error while fetching data from API"; 
    console.log(error); 
  } 
}); 
 
const statsToEmoji = { 
  intelligence: "🧠", 
  strength: "💪", 
  speed: "⚡️", 
  durability: "🏋️‍♂️", 
  power: "📊", 
  combat: "⚔️", 
}; 
 
randomSearch.addEventListener("click", async function () { 
  output.innerHTML = ` <div class="loading-container"> 
                      <div class="loading-spinner"></div> 
                      </div>`; 
  try { 
    const randomId = Math.floor(Math.random() * 731) + 1; 
    const response = await fetch(`${API_URL}/${randomId}`); 
 
    if (!response.ok) { 
      throw new Error("Network response not ok"); 
    } 
 
    hero = await response.json(); 
    console.log(hero); 
 
    output.innerHTML  = ` 
          <div class ="heroContainer" > 
            <img class ="heroImg" src = ${hero.image.url}> 
            <div class = "heroStats"> 
                <h2 class = "heroName" >${hero.name}</h2> 
                ${Object.keys(hero.powerstats) 
                  .map( 
                    (stat) => ` 
                    <div class="stat"> 
                        <span class="statEmoji">${statsToEmoji[stat]}</span> 
                        <span class="statName">${stat.toUpperCase()}:</span> 
                        <span class="statValue">${hero.powerstats[stat]}</span> 
                    </div> 
                ` 
                  ) 
                  .join("")} 
            </div> 
          </div> 
          `; 
  } catch (error) { 
    console.log("Error:", error); 
  } 
});