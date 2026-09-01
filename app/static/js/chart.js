/* =========================================================
   VARIABLES GLOBALES
========================================================= */

let chart = null;

let map = null;
let mapLayer = null;
let mapLegend = null;

let automaticCharts = [];


/* =========================================================
   OUTILS GÉNÉRAUX
========================================================= */

function getSelectedSheet() {
    const select =
        document.getElementById("sheetSelect");

    return select ? select.value : "";
}


function getSelectedCategory() {
    const select =
        document.getElementById("categorySelect");

    return select ? select.value : "";
}


function getSelectedValue() {
    const select =
        document.getElementById("valueSelect");

    return select ? select.value : "";
}


function formatNumber(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return new Intl.NumberFormat(
        "fr-BE",
        {
            maximumFractionDigits: 2
        }
    ).format(number);
}


function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


async function fetchJson(
    url,
    options = {}
) {
    const response =
        await fetch(url, options);

    let data;

    try {
        data =
            await response.json();
    } catch {
        throw new Error(
            "La réponse du serveur n'est pas valide."
        );
    }

    if (!response.ok) {
        throw new Error(
            data.detail ||
            data.error ||
            "Une erreur est survenue."
        );
    }

    return data;
}


function getFiltersQuery() {
    return new URLSearchParams();
}

/* =========================================================
   IMPORT DU FICHIER EXCEL
========================================================= */

async function uploadExcelFile() {
    const fileInput =
        document.getElementById(
            "excelFile"
        );

    const uploadButton =
        document.getElementById(
            "uploadBtn"
        );

    const message =
        document.getElementById(
            "uploadMessage"
        );

    if (!fileInput.files.length) {
        message.textContent =
            "Veuillez sélectionner un fichier Excel.";

        return;
    }

    const file =
        fileInput.files[0];

    if (
        !file.name
            .toLowerCase()
            .endsWith(".xlsx")
    ) {
        message.textContent =
            "Le fichier doit être au format .xlsx.";

        return;
    }

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    uploadButton.disabled = true;

    uploadButton.textContent =
        "Importation...";

    message.textContent = "";

    try {
        const data =
            await fetchJson(
                "/import/excel",
                {
                    method: "POST",
                    body: formData
                }
            );

        message.textContent =
            data.message ||
            "Fichier importé avec succès.";

        const sheetsLoaded = await loadSheets();

        if (sheetsLoaded) {
            showDashboardContent();
            await refreshDashboard();
        }

    } catch (error) {
        console.error(
            "Erreur import Excel :",
            error
        );

        message.textContent =
            error.message;

    } finally {
        uploadButton.disabled = false;

        uploadButton.textContent =
            "Importer";
    }
}



async function uploadGeographicReference() {

    const fileInput =
        document.getElementById("geoFile");

    const uploadButton =
        document.getElementById("geoUploadBtn");

    const message =
        document.getElementById("geoUploadMessage");

    if (!fileInput.files.length) {
        message.textContent =
            "Veuillez sélectionner un fichier géographique.";

        return;
    }

    const file =
        fileInput.files[0];

    if (
        !file.name
            .toLowerCase()
            .endsWith(".xlsx")
    ) {
        message.textContent =
            "Le référentiel doit être au format .xlsx.";

        return;
    }

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    uploadButton.disabled = true;

    uploadButton.textContent =
        "Importation...";

    message.textContent = "";

    try {

        const data =
            await fetchJson(
                "/import/geographic-reference",
                {
                    method: "POST",
                    body: formData
                }
            );

        message.textContent =
            data.message ||
            "Référentiel géographique importé avec succès.";

        populateGeoDataColumns();

        const geoSelect =
            document.getElementById(
                "geoDataColumn"
            );

        if (geoSelect?.value) {
            await loadZoneMap();
        }

    } catch (error) {

        console.error(
            "Erreur import référentiel :",
            error
        );

        message.textContent =
            error.message;

    } finally {

        uploadButton.disabled = false;

        uploadButton.textContent =
            "Importer le référentiel";
    }
}


/* =========================================================
   FEUILLES EXCEL
========================================================= */

async function loadSheets() {
    const select =
        document.getElementById(
            "sheetSelect"
        );

    select.innerHTML =
        '<option value="">Chargement...</option>';

    try {
        const data =
            await fetchJson(
                "/dashboard/sheets"
            );

        select.innerHTML = "";

        if (
            !data.sheets ||
            data.sheets.length === 0
        ) {
            select.appendChild(
                new Option(
                    "Aucune feuille disponible",
                    ""
                )
            );

            return false;
        }

        data.sheets.forEach(
            sheet => {
                select.appendChild(
                    new Option(
                        sheet,
                        sheet
                    )
                );
            }
        );

        // Sélection automatique
        // de la première feuille.
        select.value =
            data.sheets[0];

        return true;

    } catch (error) {
        console.error(
            "Erreur chargement feuilles :",
            error
        );

        select.innerHTML = "";

        select.appendChild(
            new Option(
                "Impossible de charger les feuilles",
                ""
            )
        );

        return false;
    }
}


/* =========================================================
   COLONNES
========================================================= */

function resetColumnSelects() {

    document
        .getElementById(
            "categorySelect"
        )
        .innerHTML = "";

    document
        .getElementById(
            "valueSelect"
        )
        .innerHTML =
        '<option value="">Compter les lignes</option>';



    document
        .getElementById(
            "latitudeSelect"
        )
        .innerHTML =
        '<option value="">Sélectionner</option>';

    document
        .getElementById(
            "longitudeSelect"
        )
        .innerHTML =
        '<option value="">Sélectionner</option>';

    document
        .getElementById(
            "mapLabelSelect"
        )
        .innerHTML =
        '<option value="">Libellé générique</option>';
}


function guessCoordinateColumn(
    columns,
    type
) {
    const names =
        type === "latitude"
            ? [
                "latitude",
                "lat"
            ]
            : [
                "longitude",
                "long",
                "lng",
                "lon"
            ];

    return (
        columns.find(
            column => {
                const normalized =
                    column
                        .trim()
                        .toLowerCase();

                return names.includes(
                    normalized
                );
            }
        ) || ""
    );
}


async function loadColumns() {

    resetColumnSelects();

    const sheet =
        getSelectedSheet();

    if (!sheet) {
        return false;
    }

    const params =
        new URLSearchParams({
            sheet_name: sheet
        });

    try {
        const data =
            await fetchJson(
                `/dashboard/columns?${params.toString()}`
            );

        const columns =
            data.columns || [];

        const numericColumns =
            data.numeric_columns || [];

        if (!columns.length) {
            return false;
        }

        const categorySelect =
            document.getElementById(
                "categorySelect"
            );

        const valueSelect =
            document.getElementById(
                "valueSelect"
            );

        const latitudeSelect =
            document.getElementById(
                "latitudeSelect"
            );

        const longitudeSelect =
            document.getElementById(
                "longitudeSelect"
            );

        const mapLabelSelect =
            document.getElementById(
                "mapLabelSelect"
            );

        columns.forEach(
            column => {

                categorySelect.appendChild(
                    new Option(
                        column,
                        column
                    )
                );


                latitudeSelect.appendChild(
                    new Option(
                        column,
                        column
                    )
                );

                longitudeSelect.appendChild(
                    new Option(
                        column,
                        column
                    )
                );

                mapLabelSelect.appendChild(
                    new Option(
                        column,
                        column
                    )
                );
            }
        );

        numericColumns.forEach(
            column => {

                valueSelect.appendChild(
                    new Option(
                        column,
                        column
                    )
                );
            }
        );

        /*
         * Sélection d'une première catégorie
         * non numérique si possible.
         */
        const firstCategory =
            columns.find(
                column =>
                    !numericColumns.includes(
                        column
                    )
            ) ||
            columns[0];

        if (firstCategory) {
            categorySelect.value =
                firstCategory;
        }

        /*
         * Par défaut :
         * comptage des lignes.
         */
        valueSelect.value = "";

        /*
         * Détection automatique
         * des coordonnées.
         */
        const guessedLatitude =
            guessCoordinateColumn(
                columns,
                "latitude"
            );

        const guessedLongitude =
            guessCoordinateColumn(
                columns,
                "longitude"
            );

        if (guessedLatitude) {
            latitudeSelect.value =
                guessedLatitude;
        }

        if (guessedLongitude) {
            longitudeSelect.value =
                guessedLongitude;
        }

        return true;

    } catch (error) {
        console.error(
            "Erreur chargement colonnes :",
            error
        );

        return false;
    }
}


/* =========================================================
   KPI MANUELS
========================================================= */

function resetKpis() {

    document
        .getElementById(
            "kpiRecords"
        )
        .textContent = "0";

    document
        .getElementById(
            "kpiTotal"
        )
        .textContent = "0";

    document
        .getElementById(
            "kpiCategories"
        )
        .textContent = "0";

    document
        .getElementById(
            "kpiTop"
        )
        .textContent = "-";
}


async function loadKpis() {

    const sheet =
        getSelectedSheet();

    const category =
        getSelectedCategory();

    const value =
        getSelectedValue();

    if (!sheet || !category) {
        resetKpis();
        return;
    }

    const params =
        getFiltersQuery();

    params.set(
        "sheet_name",
        sheet
    );

    params.set(
        "category_column",
        category
    );

    if (value) {
        params.set(
            "value_column",
            value
        );
    }

    try {
        const data =
            await fetchJson(
                `/dashboard/kpis?${params.toString()}`
            );

        document
            .getElementById(
                "kpiRecords"
            )
            .textContent =
            formatNumber(
                data.records
            );

        document
            .getElementById(
                "kpiTotal"
            )
            .textContent =
            formatNumber(
                data.total
            );

        document
            .getElementById(
                "kpiCategories"
            )
            .textContent =
            formatNumber(
                data.distinct_categories
            );

        document
            .getElementById(
                "kpiTop"
            )
            .textContent =
            data.top_category || "-";

    } catch (error) {
        console.error(
            "Erreur KPI :",
            error
        );

        resetKpis();
    }
}


/* =========================================================
   TABLEAU DE RÉSULTATS
========================================================= */

function resetResultsTable(
    message = "Aucune donnée affichée."
) {
    const body =
        document.getElementById(
            "resultsTableBody"
        );

    body.innerHTML = `
        <tr>
            <td colspan="2">
                ${escapeHtml(message)}
            </td>
        </tr>
    `;
}


function updateResultsTable(
    labels,
    values
) {
    const body =
        document.getElementById(
            "resultsTableBody"
        );

    body.innerHTML = "";

    if (!labels.length) {
        resetResultsTable();
        return;
    }

    labels.forEach(
        (label, index) => {

            const row =
                document.createElement(
                    "tr"
                );

            const categoryCell =
                document.createElement(
                    "td"
                );

            const valueCell =
                document.createElement(
                    "td"
                );

            categoryCell.textContent =
                label;

            valueCell.textContent =
                formatNumber(
                    values[index]
                );

            row.appendChild(
                categoryCell
            );

            row.appendChild(
                valueCell
            );

            body.appendChild(row);
        }
    );
}


/* =========================================================
   GRAPHIQUE MANUEL
========================================================= */

function destroyChart() {

    if (chart) {
        chart.destroy();
        chart = null;
    }
}


async function loadChart() {

    const sheet =
        getSelectedSheet();

    const category =
        getSelectedCategory();

    const value =
        getSelectedValue();

    if (!sheet || !category) {
        destroyChart();
        resetResultsTable();
        return;
    }

    const params =
        getFiltersQuery();

    params.set(
        "sheet_name",
        sheet
    );

    params.set(
        "category",
        category
    );

    params.set(
        "top",
        "10"
    );

    if (value) {
        params.set(
            "value",
            value
        );
    }

    try {
        const data =
            await fetchJson(
                `/dashboard/dynamic-chart?${params.toString()}`
            );

        const labels =
            data.labels || [];

        const values =
            data.values || [];

        updateResultsTable(
            labels,
            values
        );

        destroyChart();

        const context =
            document.getElementById(
                "myChart"
            );

        const selectedType =
            document.getElementById(
                "chartType"
            ).value;

        const isCircular =
            [
                "pie",
                "doughnut"
            ].includes(
                selectedType
            );

        chart =
            new Chart(
                context,
                {
                    type:
                        selectedType,

                    data: {
                        labels:
                            labels,

                        datasets: [{
                            label:
                                value
                                    ? `Total de ${value}`
                                    : "Nombre d’enregistrements",

                            data:
                                values
                        }]
                    },

                    options: {
                        responsive: true,

                        maintainAspectRatio:
                            false,

                        plugins: {
                            legend: {
                                display:
                                    isCircular
                            }
                        },

                        scales:
                            isCircular
                                ? {}
                                : {
                                    y: {
                                        beginAtZero:
                                            true
                                    }
                                }
                    }
                }
            );

    } catch (error) {
        console.error(
            "Erreur graphique :",
            error
        );

        destroyChart();

        resetResultsTable(
            error.message
        );
    }
}


/* =========================================================
   CARTE
========================================================= */

function initializeMap() {

    if (map) {
        return;
    }

    map =
        L.map("map")
            .setView(
                [
                    50.67,
                    4.61
                ],
                11
            );

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution:
                "© OpenStreetMap"
        }
    ).addTo(map);

    mapLayer =
        L.layerGroup()
            .addTo(map);
}


function clearMap() {

    initializeMap();

    if (mapLayer) {
        mapLayer.clearLayers();
    }
}


async function loadMap() {

    initializeMap();

    clearMap();

    const sheet =
        getSelectedSheet();

    const latitude =
        document.getElementById(
            "latitudeSelect"
        ).value;

    const longitude =
        document.getElementById(
            "longitudeSelect"
        ).value;

    const label =
        document.getElementById(
            "mapLabelSelect"
        ).value;

    const message =
        document.getElementById(
            "mapMessage"
        );

    if (
        !sheet ||
        !latitude ||
        !longitude
    ) {
        message.textContent =
            "Sélectionnez les colonnes latitude et longitude.";

        return;
    }

    const params =
        new URLSearchParams({
            sheet_name: sheet,
            latitude_column: latitude,
            longitude_column: longitude
        });

    if (label) {
        params.set(
            "label_column",
            label
        );
    }

    try {
        const data =
            await fetchJson(
                `/dashboard/map-points?${params.toString()}`
            );

        const points =
            data.points || [];

        if (!points.length) {
            message.textContent =
                "Aucun point géographique valide n’a été trouvé.";

            return;
        }

        const bounds = [];

        points.forEach(
            point => {

                const latitudeValue =
                    Number(
                        point.lat
                    );

                const longitudeValue =
                    Number(
                        point.lng
                    );

                if (
                    !Number.isFinite(
                        latitudeValue
                    ) ||
                    !Number.isFinite(
                        longitudeValue
                    )
                ) {
                    return;
                }

                bounds.push([
                    latitudeValue,
                    longitudeValue
                ]);

                L.circleMarker(
                    [
                        latitudeValue,
                        longitudeValue
                    ],
                    {
                        radius: 5,
                        weight: 1,
                        fillOpacity: 0.7
                    }
                )
                    .bindPopup(
                        `<strong>${
                            escapeHtml(
                                point.label
                            )
                        }</strong>`
                    )
                    .addTo(
                        mapLayer
                    );
            }
        );

        if (bounds.length) {
            map.fitBounds(
                bounds,
                {
                    padding:
                        [
                            25,
                            25
                        ]
                }
            );
        }

        message.textContent =
            `${bounds.length} point(s) affiché(s).`;

        setTimeout(
            () => {
                map.invalidateSize();
            },
            100
        );

    } catch (error) {
        console.error(
            "Erreur carte :",
            error
        );

        message.textContent =
            error.message;
    }
}


/* =========================================================
   GRAPHIQUES AUTOMATIQUES
========================================================= */

function destroyAutomaticCharts() {

    automaticCharts.forEach(
        chartInstance => {

            chartInstance.destroy();
        }
    );

    automaticCharts = [];
}


function renderAutomaticCharts(
    analyses
) {

    const container =
        document.getElementById(
            "autoChartsContainer"
        );

    if (!container) {
        console.error(
            "Élément #autoChartsContainer introuvable."
        );

        return;
    }

    destroyAutomaticCharts();

    container.innerHTML = "";

    if (
        !analyses ||
        analyses.length === 0
    ) {

        container.innerHTML = `
            <div class="card">
                <p>
                    Aucune analyse automatique pertinente
                    n'a été détectée.
                </p>
            </div>
        `;

        return;
    }

    analyses.forEach(
        (analysis, index) => {

            const card =
                document.createElement(
                    "div"
                );

            card.className = "card auto-chart-card";

            /*
             * TITRE
             */
            const title =
                document.createElement(
                    "h3"
                );

            title.textContent =
                analysis.title ||
                `Analyse ${index + 1}`;

            card.appendChild(
                title
            );

            /*
             * CONTENEUR DU GRAPHIQUE
             */

            const chartWrapper =
                document.createElement(
                    "div"
                );

            chartWrapper.className =
                "auto-chart-wrapper";


            const canvas =
                document.createElement(
                    "canvas"
                );

            canvas.id =
                `automaticChart_${index}`;

            chartWrapper.appendChild(
                canvas
            );

            card.appendChild(
                chartWrapper
            );

            /*
             * INTERPRÉTATION
             */

            const interpretation =
            document.createElement("div");

            interpretation.className =
                "auto-chart-interpretation";

            const interpretationData =
                analysis.interpretation || {};

            if (interpretationData.summary) {
                interpretation.textContent =
                    interpretationData.summary;
            } else {
                interpretation.textContent =
                    "Aucune interprétation disponible.";
            }

            card.appendChild(interpretation);


            /*
             * INFORMATIONS
             */
            const info =
                document.createElement(
                    "p"
                );

            info.className =
                "auto-chart-info";

            const calculationText =
                analysis.calculation ===
                "sum"
                    ? "Somme"
                    : "Comptage";

            let relevanceText = "Pertinence moyenne";

            const score = Number(
                analysis.score ?? 0
            );

            if (score >= 70) {
                relevanceText = "Pertinence élevée";
            } else if (score >= 40) {
                relevanceText = "Pertinence moyenne";
            } else {
                relevanceText = "Pertinence faible";
            }

            info.textContent =
                `${calculationText} • ${relevanceText}`;

            card.appendChild(
                info
            );


            /*
             * AJOUT DE LA CARTE
             */


            container.appendChild(
                card
            );

            /*
             * TYPE DÉCIDÉ PAR PYTHON
             */
            const chartType =
                analysis.chart_type ||
                "bar";

            const isCircular =
                chartType === "doughnut" ||
                chartType === "pie";

            /*
             * CONFIGURATION DES AXES
             */
            const chartOptions = {
                responsive: true,

                maintainAspectRatio:
                    false,

                plugins: {
                    legend: {
                        display: isCircular,
                        position: "bottom",

                        labels: {
                            font: {
                                size: 10
                            },

                            boxWidth: 12,
                            boxHeight: 9,
                            padding: 10
                        }
                    },

                    tooltip: {
                        enabled:
                            true
                    }
                }
            };

            /*
             * Barres horizontales
             * pour meilleure lisibilité.
             */
            if (!isCircular) {

                chartOptions.indexAxis =
                    "y";

                chartOptions.scales = {
                    x: {
                        beginAtZero: true,

                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    },

                    y: {
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    }
                };

            } else {

                chartOptions.scales = {};
            }

            /*
             * CRÉATION CHART.JS
             */
            const chartInstance =
                new Chart(
                    canvas,
                    {
                        type:
                            chartType,

                        data: {
                            labels:
                                analysis.labels ||
                                [],

                            datasets: [{
                                label:
                                    calculationText,

                                data:
                                    analysis.values ||
                                    []
                            }]
                        },

                        options:
                            chartOptions
                    }
                );

            automaticCharts.push(
                chartInstance
            );
        }
    );
}


/* =========================================================
   ANALYSE AUTOMATIQUE
========================================================= */

async function loadAutoAnalysis() {

    const sheet =
        getSelectedSheet();

    const autoButton =
        document.getElementById("autoAnalysisBtn");

    const message =
        document.getElementById(
            "autoAnalysisMessage"
        );

    const detectedBlock =
        document.getElementById(
            "autoDetectedColumns"
        );

    const kpiBlock =
        document.getElementById(
            "autoKpis"
        );

    const chartsBlock =
        document.getElementById(
            "autoCharts"
        );

    const container =
        document.getElementById(
            "autoChartsContainer"
        );

    /*
     * Vérification des éléments HTML.
     */
    if (
        !message ||
        !detectedBlock ||
        !kpiBlock ||
        !chartsBlock ||
        !container
    ) {
        console.error(
            "Un élément HTML nécessaire à l'analyse automatique est introuvable."
        );

        return;
    }

    if (!sheet) {
        message.textContent =
            "Veuillez sélectionner une feuille Excel.";

        return;
    }

    /*
     * État de chargement.
     */
    message.textContent =
        "Analyse en cours...";

    detectedBlock.style.display =
        "none";

    kpiBlock.style.display =
        "none";

    chartsBlock.style.display =
        "none";
    setTimeout(() => {

        chartsBlock.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }, 150);

    destroyAutomaticCharts();

    container.innerHTML = "";

    autoButton.disabled = true;
    autoButton.textContent = "Analyse en cours...";

    try {

        const params =
            new URLSearchParams({
                sheet_name: sheet
            });

        const data =
            await fetchJson(
                `/dashboard/auto-analysis?${params.toString()}`
            );

        console.log(
            "Résultat analyse automatique :",
            data
        );

        if (!data.has_data) {

            message.textContent =
                data.message ||
                "Aucune donnée disponible.";

            return;
        }

        /*
         * COLONNES DÉTECTÉES
         */
        const detected =
            data.detected_columns ||
            {};

        document
            .getElementById(
                "autoCategoryColumn"
            )
            .textContent =
            detected.category ||
            "Non détectée";

        document
            .getElementById(
                "autoNumericColumn"
            )
            .textContent =
            detected.numeric ||
            "Comptage des lignes";

        document
            .getElementById(
                "autoDateColumn"
            )
            .textContent =
            detected.date ||
            "Non détectée";

        detectedBlock.style.display =
            "grid";

        /*
         * KPI AUTOMATIQUES
         */
        const kpis =
            data.kpis || {};

        document
            .getElementById(
                "autoRecords"
            )
            .textContent =
            formatNumber(
                kpis.records || 0
            );

        document
            .getElementById(
                "autoTotal"
            )
            .textContent =
            formatNumber(
                kpis.total || 0
            );

        document
            .getElementById(
                "autoCategories"
            )
            .textContent =
            formatNumber(
                kpis.distinct_categories ||
                0
            );

        document
            .getElementById(
                "autoTopCategory"
            )
            .textContent =
            kpis.top_category ||
            "-";

        kpiBlock.style.display =
            "grid";

        /*
         * GRAPHIQUES AUTOMATIQUES
         */
        const analyses =
            data.automatic_analyses ||
            [];

        console.log(
            "Analyses automatiques reçues :",
            analyses
        );

        renderAutomaticCharts(
            analyses
        );

        /*
         * Rendre le bloc visible.
         */
        chartsBlock.style.display =
            "block";

        setTimeout(() => {

            chartsBlock.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        }, 150);

        /*
         * Message final.
         */
        message.textContent =
            `${analyses.length} analyse(s) automatique(s) générée(s).`;

        } catch (error) {

            console.error(error);

            message.textContent =
                `Erreur : ${error.message}`;

        } finally {

            autoButton.disabled = false;

            autoButton.textContent =
                "Lancer l’analyse automatique";
        }
    }


/* =========================================================
   ACTUALISATION
========================================================= */

async function refreshAnalysis() {

    await Promise.all([
        loadKpis(),
        loadChart()
    ]);
}


async function loadSheetSummary() {
    const sheet = getSelectedSheet();

    const section =
        document.getElementById("sheetSummarySection");

    const rowsElement =
        document.getElementById("summaryRows");

    const columnsElement =
        document.getElementById("summaryColumns");

    const capabilities =
        document.getElementById("sheetCapabilities");

    if (!sheet || !section) {
        return;
    }

    try {
        const params = new URLSearchParams({
            sheet_name: sheet
        });

        const data = await fetchJson(
            `/dashboard/auto-analysis?${params.toString()}`
        );

        if (!data.has_data) {
            section.style.display = "none";
            return;
        }

        const profile = data.profile || [];
        const kpis = data.kpis || {};

        rowsElement.textContent =
            formatNumber(kpis.records || 0);

        columnsElement.textContent =
            formatNumber(profile.length);

        const roles = profile.map(
            column => column.role
        );

        const messages = [];

        const hasNumeric =
            roles.includes("measure") ||
            roles.includes("numeric");

        const hasTemporal =
            roles.includes("date") ||
            roles.includes("temporal");

        const hasLatitude =
            roles.includes("latitude");

        const hasLongitude =
            roles.includes("longitude");

        const hasLocation =
            roles.includes("location");

        if (hasNumeric) {
            messages.push(
                "✓ Données numériques détectées"
            );
        }

        if (hasTemporal) {
            messages.push(
                "✓ Données temporelles détectées"
            );
        }

        if (hasLatitude && hasLongitude) {
            messages.push(
                "✓ Coordonnées géographiques détectées"
            );
        } else if (hasLocation) {
            messages.push(
                "✓ Informations de localisation détectées"
            );
        }

        if (!messages.length) {
            messages.push(
                "Aucun type particulier de données détecté."
            );
        }

        capabilities.innerHTML =
            messages
                .map(message => `
                    <span class="data-capability">
                        ${message}
                    </span>
                `)
                .join("");

        section.style.display = "block";

    } catch (error) {
        console.error(
            "Erreur résumé feuille :",
            error
        );

        section.style.display = "none";
    }
}

async function refreshDashboard() {

    resetKpis();

    destroyChart();

    resetResultsTable();

    /*
     * Nettoyage de l'analyse automatique
     * lors d'un changement de feuille.
     */
    destroyAutomaticCharts();

    const autoDetectedBlock =
        document.getElementById(
            "autoDetectedColumns"
        );

    const autoKpisBlock =
        document.getElementById(
            "autoKpis"
        );

    const autoChartsBlock =
        document.getElementById(
            "autoCharts"
        );

    const autoMessage =
        document.getElementById(
            "autoAnalysisMessage"
        );

    if (autoDetectedBlock) {
        autoDetectedBlock.style.display =
            "none";
    }

    if (autoKpisBlock) {
        autoKpisBlock.style.display =
            "none";
    }

    if (autoChartsBlock) {
        autoChartsBlock.style.display =
            "none";
    }

    if (autoMessage) {
        autoMessage.textContent =
            "Cliquez sur « Lancer l’analyse automatique » pour générer les résultats.";
    }

    /*
     * Chargement des colonnes.
     */
    const columnsLoaded =
        await loadColumns();

    if (!columnsLoaded) {
        return;
    }

    await loadSheetSummary();
    await refreshAnalysis();

    await loadMap();

}

function toggleManualAnalysis() {

    const section =
        document.getElementById(
            "manualAnalysisSection"
        );

    const visualizations =
        document.getElementById(
            "manualVisualizations"
        );

    const results =
        document.getElementById(
            "manualResults"
        );

    const button =
        document.getElementById(
            "toggleManualAnalysis"
        );

    if (!section || !button) {
        return;
    }

    const isHidden =
        section.style.display === "none";

    if (isHidden) {

        // Afficher les paramètres avancés
        section.style.display = "block";

        // Afficher graphique + cartographie
        if (visualizations) {
            visualizations.style.display = "grid";
        }

        // Afficher le tableau détaillé
        if (results) {
            results.style.display = "block";
        }

        button.textContent =
            "Masquer les options avancées";


        /*
         * Leaflet peut avoir été initialisé
         * pendant que la carte était masquée.
         * On recalcule donc sa taille.
         */
        setTimeout(() => {

            if (map) {
                map.invalidateSize();
            }

        }, 150);

    } else {

        // Masquer les paramètres
        section.style.display = "none";

        // Masquer graphique + carte
        if (visualizations) {
            visualizations.style.display = "none";
        }

        // Masquer le tableau
        if (results) {
            results.style.display = "none";
        }

        button.textContent =
            "Afficher les options avancées";
    }
}


/* =========================================================
   ÉVÉNEMENTS
========================================================= */

function registerEvents() {

    const autoButton =
        document.getElementById(
            "autoAnalysisBtn"
        );

    if (autoButton) {
        autoButton.addEventListener(
            "click",
            loadAutoAnalysis
        );
    }

    const manualButton =
        document.getElementById(
            "toggleManualAnalysis"
        );

    if (manualButton) {
        manualButton.addEventListener(
            "click",
            toggleManualAnalysis
        );
    }

    const geoUploadButton =
        document.getElementById(
            "geoUploadBtn"
        );

    if (geoUploadButton) {
        geoUploadButton.addEventListener(
            "click",
            uploadGeographicReference
        );
    }

    const geoDataColumn =
        document.getElementById(
            "geoDataColumn"
        );

    if (geoDataColumn) {
        geoDataColumn.addEventListener(
            "change",
            async () => {

                await checkGeoCompatibility();

                await loadZoneMap();
            }
        );
    }

    document
        .getElementById(
            "uploadBtn"
        )
        .addEventListener(
            "click",
            uploadExcelFile
        );

    document
        .getElementById(
            "sheetSelect"
        )
        .addEventListener(
            "change",
            refreshDashboard
        );

    document
        .getElementById(
            "categorySelect"
        )
        .addEventListener(
            "change",
            refreshAnalysis
        );

    document
        .getElementById(
            "valueSelect"
        )
        .addEventListener(
            "change",
            refreshAnalysis
        );

    document
        .getElementById(
            "chartType"
        )
        .addEventListener(
            "change",
            loadChart
        );



    document
        .getElementById(
            "latitudeSelect"
        )
        .addEventListener(
            "change",
            loadMap
        );

    document
        .getElementById(
            "longitudeSelect"
        )
        .addEventListener(
            "change",
            loadMap
        );

    document
        .getElementById(
            "mapLabelSelect"
        )
        .addEventListener(
            "change",
            loadMap
        );
}


/* =========================================================
   DÉMARRAGE
========================================================= */

async function initializeDashboard() {

    registerEvents();

    hideDashboardContent();

}


document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);

function showDashboardContent() {

    const content =
        document.getElementById(
            "dashboardContent"
        );

    if (content) {
        content.style.display = "block";
    }
}


function hideDashboardContent() {

    const content =
        document.getElementById(
            "dashboardContent"
        );

    if (content) {
        content.style.display = "none";
    }
}

function populateGeoDataColumns() {

    const geoSelect =
        document.getElementById("geoDataColumn");

    const mappingOptions =
        document.getElementById("geoMappingOptions");

    const categorySelect =
        document.getElementById("categorySelect");

    if (
        !geoSelect ||
        !mappingOptions ||
        !categorySelect
    ) {
        return;
    }

    /*
     * Réinitialisation
     */
    geoSelect.innerHTML = `
        <option value="">
            Sélectionnez une colonne
        </option>
    `;

    /*
     * On récupère les colonnes déjà présentes
     * dans le sélecteur d'analyse.
     */
    Array.from(
        categorySelect.options
    ).forEach(option => {

        if (!option.value) {
            return;
        }

        const newOption =
            document.createElement("option");

        newOption.value =
            option.value;

        newOption.textContent =
            option.textContent;

        geoSelect.appendChild(
            newOption
        );
    });

    /*
     * Affichage du bloc
     */
    mappingOptions.style.display =
        "block";
}

async function loadZoneMap() {

    const sheet =
        getSelectedSheet();

    const dataColumn =
        document.getElementById(
            "geoDataColumn"
        )?.value;

    const message =
        document.getElementById(
            "mapMessage"
        );

    if (!sheet || !dataColumn) {

        if (message) {
            message.textContent =
                "Sélectionnez une colonne géographique.";
        }

        return;
    }

    initializeMap();
    clearMap();

    const params =
        new URLSearchParams({
            sheet_name: sheet,
            data_column: dataColumn
        });

    try {

        const data =
            await fetchJson(
                `/dashboard/map-zones?${params.toString()}`
            );

        const points =
            data.points || [];

        if (!points.length) {

            if (message) {
                message.textContent =
                    "Aucune zone géographique correspondante.";
            }

            return;
        }

        const bounds = [];

        /*
         * =====================================================
         * AFFICHAGE DES ZONES
         * =====================================================
         */
        points.forEach(point => {

            const lat =
                Number(point.lat);

            const lng =
                Number(point.lng);

            const count =
                Number(point.count || 0);

            /*
             * Vérification des coordonnées
             */
            if (
                !Number.isFinite(lat) ||
                !Number.isFinite(lng)
            ) {
                return;
            }

            bounds.push([
                lat,
                lng
            ]);


            /*
             * Taille du cercle selon le nombre de faits
             */
            const radius =
                Math.max(
                    6,
                    Math.min(
                        22,
                        Math.sqrt(count) * 1.3
                    )
                );


            /*
             * Couleur selon le nombre de faits
             */
            let circleColor;

            if (count >= 150) {

                circleColor = "#c0392b";

            } else if (count >= 100) {

                circleColor = "#e67e22";

            } else if (count >= 50) {

                circleColor = "#f1c40f";

            } else {

                circleColor = "#3498db";
            }


            /*
             * Création du cercle
             */
            L.circleMarker(
                [lat, lng],
                {
                    radius: radius,

                    color: "#ffffff",

                    fillColor: circleColor,

                    weight: 2,

                    opacity: 1,

                    fillOpacity: 0.78
                }
            )
            .bindPopup(`
                <strong>
                    ${escapeHtml(point.label)}
                </strong>

                <br>

                ${formatNumber(count)} fait(s)
            `)
            .addTo(mapLayer);

        });


        /*
         * =====================================================
         * LÉGENDE
         * Créée une seule fois après les points
         * =====================================================
         */

        if (mapLegend) {

            map.removeControl(
                mapLegend
            );

            mapLegend = null;
        }


        mapLegend =
            L.control({
                position: "bottomright"
            });


        mapLegend.onAdd = function () {

            const div =
                L.DomUtil.create(
                    "div",
                    "map-legend"
                );

            div.innerHTML = `
                <strong>
                    Nombre de faits
                </strong>

                <div>
                    <span class="legend-dot blue"></span>
                    Moins de 50
                </div>

                <div>
                    <span class="legend-dot yellow"></span>
                    50 à 99
                </div>

                <div>
                    <span class="legend-dot orange"></span>
                    100 à 149
                </div>

                <div>
                    <span class="legend-dot red"></span>
                    150 et plus
                </div>

                <small>
                    La taille du cercle varie également
                    selon le nombre de faits.
                </small>
            `;

            return div;
        };


        mapLegend.addTo(
            map
        );


        /*
         * =====================================================
         * AJUSTEMENT DU ZOOM
         * =====================================================
         */

        if (bounds.length) {

            map.fitBounds(
                bounds,
                {
                    padding: [
                        30,
                        30
                    ]
                }
            );
        }


        /*
         * Message utilisateur
         */
        if (message) {

            message.textContent =
                `${bounds.length} zone(s) affichée(s).`;
        }


        /*
         * Correction de la taille Leaflet
         */
        setTimeout(() => {

            if (map) {
                map.invalidateSize();
            }

        }, 100);


    } catch (error) {

        console.error(
            "Erreur carte par zone :",
            error
        );

        if (message) {

            message.textContent =
                error.message;
        }
    }
}

async function checkGeoCompatibility() {

    const sheet =
        getSelectedSheet();

    const dataColumn =
        document.getElementById(
            "geoDataColumn"
        )?.value;

    const message =
        document.getElementById(
            "geoCompatibilityMessage"
        );

    if (!message) {
        return;
    }

    if (!sheet || !dataColumn) {
        message.style.display = "none";
        return;
    }

    try {

        const params =
            new URLSearchParams({
                sheet_name: sheet,
                data_column: dataColumn
            });

        const data =
            await fetchJson(
                `/dashboard/map-zones?${params.toString()}`
            );

        const matchedCount =
            data.count || 0;

        const unmatched =
            data.unmatched_zones || [];

        message.style.display = "block";

        /*
         * Correspondance complète
         */
        if (
            matchedCount > 0 &&
            unmatched.length === 0
        ) {

            message.className =
                "geo-compatibility-message success";

            message.innerHTML = `
                <strong>
                    ✓ Référentiel compatible
                </strong>

                <br>

                La colonne
                « ${escapeHtml(dataColumn)} »
                correspond au référentiel géographique.

                <br>

                ${matchedCount} zone(s) reconnue(s),
                aucune zone non reconnue.
            `;

            return;
        }


        /*
         * Correspondance partielle
         */
        if (matchedCount > 0) {

            message.className =
                "geo-compatibility-message warning";

            message.innerHTML = `
                <strong>
                    ⚠ Correspondance partielle
                </strong>

                <br>

                ${matchedCount} zone(s) reconnue(s)
                et
                ${unmatched.length} zone(s)
                non reconnue(s).
            `;

            return;
        }


        /*
         * Aucune correspondance
         */
        message.className =
            "geo-compatibility-message error";

        message.innerHTML = `
            <strong>
                ✕ Référentiel incompatible
            </strong>

            <br>

            Aucune valeur de la colonne
            « ${escapeHtml(dataColumn)} »
            ne correspond au référentiel géographique.
        `;

    } catch (error) {

        console.error(
            "Erreur vérification référentiel :",
            error
        );

        message.style.display =
            "block";

        message.className =
            "geo-compatibility-message error";

        message.textContent =
            error.message ||
            "Impossible de vérifier la correspondance du référentiel.";
    }
}