document.addEventListener("DOMContentLoaded", function(){

    console.log("JS chargé");

    const form = document.querySelector("form");

    if (!form) return;

    const champPseudo = document.querySelector("input[name='utilisateur']");

    const champmotsdepasse = document.querySelector("input[name='mots_de_passe']");

    const champconfirmemotsdepasse = document.querySelector("input[name='confirme_mots_de_passe']");

    function validerChamp(champ, condition, message) {

        let erreur = champ.parentElement.querySelector(".message-erreur");

        if(!condition) {
            if(!erreur) {
                erreur = document.createElement("p");
                erreur.classList.add("message-erreur");
                champ.parentElement.appendChild(erreur);
            }
            erreur.textContent = message;

            champ.classList.add("champ-invalide");

            return false;
        } else {

            if (erreur) erreur.remove();

            champ.classList.remove("champ-invalide");

            return true;
        }

    }
    
    champmotsdepasse.addEventListener("input", function() {
        validerChamp(
            champmotsdepasse,
            champmotsdepasse.value.trim().lenght >= 8,
            "Le mots de passe doit contenir au moins 8 caracteres");
    });

    champconfirmemotsdepasse.addEventListener("input", function() {
        validerChamp(
            champconfirmemotsdepasse,
            champconfirmemotsdepasse.value == champmotsdepasse.value,
            "Les mots de passe ne correespondent pas");
    });

    form.addEventListener("submit", function(evenement){

        const mots_de_passe_ok = validerChamp(
            champmotsdepasse,
            champmotsdepasse.value.trim().length >= 8,
            "Le mots de passe doit contenir au moins 10 caracteres");

        const confirme_mots_de_passe_ok = validerChamp(
            champconfirmemotsdepasse,
            champconfirmemotsdepasse.value == champmotsdepasse.value,
            "Les mots de passe ne correespondent pas");
        
        if (!mots_de_passe_ok || !confirme_mots_de_passe_ok) {
            evenement.preventDefault();
            return;
        }

    });

    

});