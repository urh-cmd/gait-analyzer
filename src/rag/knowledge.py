"""
Haile - Clinical Knowledge Base
================================
Medical knowledge base for gait analysis with reference values and clinical guidelines.
"""

from typing import List, Dict
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class ClinicalDocument:
    """A clinical reference document."""
    id: str
    title: str
    category: str
    content: str
    tags: List[str]
    references: List[str]


class ClinicalKnowledgeBase:
    """
    Clinical knowledge base for gait analysis.
    Contains reference values, pathological patterns, and clinical recommendations.
    """
    
    def __init__(self):
        self.documents: List[ClinicalDocument] = []
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load the clinical knowledge base."""
        
        # ===== NORMWERTE =====
        self.documents.append(ClinicalDocument(
            id="norm_temporal",
            title="Temporale Gangparameter - Normwerte",
            category="reference_values",
            content="""
            Temporale Parameter der Ganganalyse (Erwachsene, gesunde Population):
            
            - Cadenz (Schrittfrequenz): 100-120 Schritte/min
              * Niedrig: <90 Schritte/min (verlangsamter Gang)
              * Hoch: >130 Schritte/min (hastiger Gang)
            
            - Schrittzeit: 0.9-1.1 Sekunden pro Schritt
              * Asymmetrie >10% zwischen links/rechts ist auffällig
            
            - Gangzyklus-Phasen:
              * Stance Phase (Standphase): 60% des Zyklus
              * Swing Phase (Schwungphase): 40% des Zyklus
              * Doppelstandphase: 10-20% (nimmt mit Geschwindigkeit ab)
              * Einfachstandphase: ~40%
            
            - Schrittanzahl pro Minute bei normaler Geschwindigkeit: 100-120
            """,
            tags=["temporal", "reference", "cadence", "gait_cycle"],
            references=["Perry & Burnfield, Gait Analysis, 2010", "Whittle, Gait Analysis, 2014"]
        ))
        
        self.documents.append(ClinicalDocument(
            id="norm_spatial",
            title="Räumliche Gangparameter - Normwerte",
            category="reference_values",
            content="""
            Räumliche Parameter der Ganganalyse (Erwachsene):
            
            - Schrittlänge: 60-80 cm (abhängig von Körpergröße)
              * Formel: ~0.413 × Körpergröße (cm) für Männer
              * Formel: ~0.413 × Körpergröße (cm) für Frauen
              * Asymmetrie >10% ist klinisch relevant
            
            - Schrittbreite (Base of Support): 5-10 cm
              * Erhöht bei Gleichgewichtsstörungen (>15 cm)
              * Verringert bei Parkinson (<5 cm)
            
            - Ganglinie (Foot Progression Angle): 5-10° Außenrotation
            
            - Körpergrößen-Normalisierung:
              * Schrittweite / Körpergröße ≈ 0.66 (dimensionslos)
            """,
            tags=["spatial", "reference", "step_length", "stride"],
            references=["Perry & Burnfield, Gait Analysis, 2010"]
        ))
        
        self.documents.append(ClinicalDocument(
            id="norm_symmetry",
            title="Symmetrie-Indizes - Bewertung",
            category="reference_values",
            content="""
            Symmetrie-Bewertung in der Ganganalyse:
            
            - Symmetrie-Index (SI):
              * Formel: SI = |Links - Rechts| / ((Links + Rechts) / 2) × 100
              * Normal: <10% (symmetrisch)
              * Leicht auffällig: 10-15%
              * Deutlich auffällig: >15%
            
            - Phasen-Symmetrie:
              * Swing-Phase-Symmetrie: <5% Unterschied ideal
              * Stance-Phase-Symmetrie: <5% Unterschied ideal
              * >15% Unterschied ist klinisch signifikant
            
            - Klinische Interpretation:
              * Asymmetrie kann hinweisen auf:
                - Schmerz (antalgischer Gang)
                - Muskelschwäche
                - Neurologische Störung
                - Strukturelle Beinlängendifferenz
            """,
            tags=["symmetry", "index", "asymmetry", "pathology"],
            references=["Zifchock et al., Gait & Posture, 2008"]
        ))
        
        self.documents.append(ClinicalDocument(
            id="norm_kinematic",
            title="Kinematische Normwerte - Gelenkwinkel",
            category="reference_values",
            content="""
            Gelenkwinkel-Normwerte während des Gangs:
            
            - Kniegelenk:
              * Initial Contact: 0-5° Flexion
              * Loading Response: 15-20° Flexion (Shock Absorption)
              * Mid-Stance: 0-5° Flexion
              * Terminal Swing: 30-40° Flexion (Preparation for contact)
              * Maximal während Swing: 60-70° Flexion
              * <50° = reduzierte Flexion (Steife/Kontraktur)
              * >75° = Hyperflexion (Instabilität)
            
            - Hüftgelenk:
              * Extension in Terminal Stance: 10-20°
              * Flexion in Initial Swing: 20-30°
              * Range of Motion: ~30-40°
            
            - Sprunggelenk:
              * Dorsiflexion bei Initial Contact: 0-5°
              * Plantarflexion in Push-off: 15-20°
              * Dorsiflexion während Swing: 0-5°
            """,
            tags=["kinematic", "joint_angles", "knee", "hip", "ankle"],
            references=["Perry & Burnfield, Gait Analysis, 2010"]
        ))
        
        # ===== PATHOLOGISCHE MUSTER =====
        self.documents.append(ClinicalDocument(
            id="pathology_antalgic",
            title="Antalgischer Gang (Schonhinken)",
            category="pathology",
            content="""
            Antalgischer Gang - Schmerzhinkeln:
            
            Merkmale:
            - Verkürzte Standphase auf der betroffenen Seite
            - Verlängerte Schwungphase auf der betroffenen Seite
            - Reduzierte Cadenz
            - Oft asymmetrische Schrittlänge
            
            Ursachen:
            - Arthrose (Hüfte, Knie, Sprunggelenk)
            - Frakturen/Stressfrakturen
            - Weichteilverletzungen
            - Post-operative Zustände
            
            Klinische Hinweise:
            - Patient vermeidet Belastung
            - Gesichtsausdruck zeigt Schmerz
            - Hinken korreliert mit Schmerzintensität
            
            Empfehlungen:
            - Schmerzmanagement
            - Gehhilfe temporär
            - Physiotherapie nach Schmerzlinderung
            """,
            tags=["antalgic", "pain", "pathology", "limp"],
            references=["Clinical Gait Analysis, 2019"]
        ))
        
        self.documents.append(ClinicalDocument(
            id="pathology_trendelenburg",
            title="Trendelenburg-Gang",
            category="pathology",
            content="""
            Trendelenburg-Gang - Hüftabduktoren-Schwäche:
            
            Merkmale:
            - Beckenabsenkung auf der kontralateralen Seite während Standphase
            - Rumpfbeugung zur betroffenen Seite (Kompensation)
            - Watschelnder Gang bei bilateraler Betroffenheit
            
            Ursachen:
            - M. gluteus medius/minimus Schwäche
            - Superior Gluteal Nerve Injury
            - Hüftdysplasie
            - Post-Hüft-OP
            
            Test:
            - Trendelenburg-Test: Einbeinstand >30 Sekunden
            - Positiv wenn Becken auf Gegenseite absinkt
            
            Empfehlungen:
            - Hüftabduktoren-Strengthening
            - Gangschulung
            - Ggf. Orthesenversorgung
            """,
            tags=["trendelenburg", "hip", "abductor", "weakness"],
            references=["Clinical Gait Analysis, 2019"]
        ))
        
        self.documents.append(ClinicalDocument(
            id="pathology_steppage",
            title="Steppage-Gang (Fall Foot)",
            category="pathology",
            content="""
            Steppage-Gang - Peroneusparese:
            
            Merkmale:
            - Übermäßige Hüft- und Knieflexion während Swing
            - "Stepping over" Bewegung
            - Foot slap bei Initial Contact
            - Erhöhte Schritthöhe
            
            Ursachen:
            - N. peroneus communis Läsion
            - L5 Radikulopathie
            - Distal Muscle Weakness
            - Charcot-Marie-Tooth Disease
            
            Klinische Hinweise:
            - Fußheberschwäche
            - Sensibilitätsstörung am Fußrücken
            - Ggf. Atrophie der Tibialis anterior
            
            Empfehlungen:
            - Fußheberorthese (AFO)
            - Neurologische Abklärung
            - EMG/NLG-Diagnostik
            """,
            tags=["steppage", "foot_drop", "peroneal", "neurology"],
            references=["Clinical Gait Analysis, 2019"]
        ))
        
        # ===== EMPFEHLUNGEN =====
        self.documents.append(ClinicalDocument(
            id="recommendation_general",
            title="Allgemeine Therapieempfehlungen",
            category="recommendations",
            content="""
            Allgemeine Empfehlungen basierend auf Ganganalyse-Ergebnissen:
            
            Bei asymmetrischem Gang (SI >10%):
            - Ausführliche Anamnese (Schmerz, Trauma, OP)
            - Manuelle Muskeltests
            - Ggf. bildgebende Diagnostik
            - Gezielte Physiotherapie
            
            Bei reduzierter Cadenz (<90/min):
            - Kardiovaskuläre Fitness prüfen
            - Gangtempo-Training
            - Ausdauerübungen
            - Progressives Gehtraining
            
            Bei erhöhter Cadenz (>130/min):
            - Gleichgewichtstraining
            - Gangverlangsamung üben
            - Propriozeption verbessern
            
            Bei reduzierter Knieflexion (<50°):
            - Kniegelenks-Mobilisation
            - Quadriceps/Hamstring Dehnung
            - Swing-Phase Training
            - Ggf. orthopädische Abklärung
            """,
            tags=["recommendations", "therapy", "physiotherapy"],
            references=["Physical Therapy Guidelines, 2020"]
        ))
    
    def get_documents_by_category(self, category: str) -> List[ClinicalDocument]:
        """Get all documents in a category."""
        return [doc for doc in self.documents if doc.category == category]
    
    def get_documents_by_tags(self, tags: List[str]) -> List[ClinicalDocument]:
        """Get documents matching any of the given tags."""
        result = []
        for doc in self.documents:
            if any(tag in doc.tags for tag in tags):
                result.append(doc)
        return result
    
    def search(self, query: str) -> List[ClinicalDocument]:
        """Simple keyword search."""
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            score = 0
            content_lower = doc.content.lower()
            title_lower = doc.title.lower()
            
            # Check title
            if query_lower in title_lower:
                score += 3
            
            # Check content
            if query_lower in content_lower:
                score += 2
            
            # Check tags
            for tag in doc.tags:
                if query_lower in tag.lower():
                    score += 1
            
            if score > 0:
                results.append((score, doc))
        
        # Sort by score
        results.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in results]
    
    def get_all_content(self) -> str:
        """Get all document content as a single string for embedding."""
        return "\n\n".join([
            f"### {doc.title}\n{doc.content}"
            for doc in self.documents
        ])
    
    def to_dict_list(self) -> List[Dict]:
        """Convert all documents to dictionary format."""
        return [
            {
                "id": doc.id,
                "title": doc.title,
                "category": doc.category,
                "content": doc.content,
                "tags": doc.tags,
                "references": doc.references
            }
            for doc in self.documents
        ]
    
    def save_to_json(self, path: str):
        """Save knowledge base to JSON file."""
        data = self.to_dict_list()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_json(cls, path: str) -> 'ClinicalKnowledgeBase':
        """Load knowledge base from JSON file."""
        kb = cls()
        kb.documents = []
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            kb.documents.append(ClinicalDocument(
                id=item['id'],
                title=item['title'],
                category=item['category'],
                content=item['content'],
                tags=item['tags'],
                references=item['references']
            ))
        
        return kb
