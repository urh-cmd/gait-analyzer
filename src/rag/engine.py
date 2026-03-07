"""
Haile - RAG Engine
===================
Retrieval-Augmented Generation for clinical gait analysis reports.
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json

from .knowledge import ClinicalKnowledgeBase, ClinicalDocument
from .providers import LLMProvider, get_provider, OpenAIProvider, QwenProvider, AnthropicProvider


@dataclass
class RAGConfig:
    """Configuration for RAG engine."""
    provider: str = "openai"  # openai, qwen, anthropic
    model: Optional[str] = None
    api_key: Optional[str] = None
    include_references: bool = True
    max_context_docs: int = 5
    temperature: float = 0.3


@dataclass
class GaitAnalysisInput:
    """Input data for RAG-based analysis."""
    patient_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None  # cm
    weight: Optional[float] = None  # kg
    chief_complaint: Optional[str] = None
    pain_location: Optional[List[str]] = None
    pain_intensity: Optional[int] = None  # 0-10
    gait_metrics: Dict[str, Any] = None
    keypoints_summary: Optional[Dict] = None


class RAGEngine:
    """
    RAG Engine for generating clinical gait analysis reports.
    
    Combines patient data, gait metrics, and clinical knowledge base
    to generate professional, evidence-based reports using LLMs.
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.knowledge_base = ClinicalKnowledgeBase()
        self._provider: Optional[LLMProvider] = None
        self._vector_store = None
        self._embeddings = None
    
    def _get_provider(self) -> LLMProvider:
        """Get or create the LLM provider."""
        if self._provider is None:
            model = self.config.model
            if model is None:
                # Default models per provider
                default_models = {
                    "openai": "gpt-4o-mini",
                    "qwen": "qwen-max",
                    "anthropic": "claude-3-haiku-20240307",
                }
                model = default_models.get(self.config.provider)
            
            self._provider = get_provider(self.config.provider, self.config.api_key)
            if hasattr(self._provider, 'model'):
                self._provider.model = model
        
        return self._provider
    
    def _setup_vector_store(self):
        """Setup vector store for semantic search."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Initialize ChromaDB
            persist_dir = Path("data/rag_index")
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            client = chromadb.PersistentClient(path=str(persist_dir))
            
            # Get or create collection
            self._vector_store = client.get_or_create_collection(
                name="clinical_knowledge",
                metadata={"description": "Clinical gait analysis knowledge base"}
            )
            
            # Check if we need to populate
            if self._vector_store.count() == 0:
                self._populate_vector_store()
                
        except ImportError:
            print("ChromaDB not available, using keyword search fallback")
            self._vector_store = None
    
    def _get_embeddings(self):
        """Get embedding model."""
        if self._embeddings is None:
            try:
                from chromadb.utils import embedding_functions
                self._embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            except Exception:
                self._embeddings = None
        return self._embeddings
    
    def _populate_vector_store(self):
        """Populate vector store with knowledge base documents."""
        if self._vector_store is None:
            return
        
        embeddings_fn = self._get_embeddings()
        
        for doc in self.knowledge_base.documents:
            # Create document text
            doc_text = f"Title: {doc.title}\n\n{doc.content}"
            
            # Get embedding
            if embeddings_fn:
                embedding = embeddings_fn([doc_text])[0]
            else:
                # Fallback: use simple hash-based "embedding"
                embedding = [hash(doc_text) % 10000 / 10000.0] * 384
            
            # Add to collection
            self._vector_store.add(
                documents=[doc_text],
                metadatas=[{
                    "id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "tags": ",".join(doc.tags)
                }],
                ids=[doc.id],
                embeddings=[embedding] if embeddings_fn else None
            )
    
    def _retrieve_context(self, query: str) -> List[ClinicalDocument]:
        """Retrieve relevant documents from knowledge base."""
        if self._vector_store is not None:
            # Semantic search
            try:
                embeddings_fn = self._get_embeddings()
                
                if embeddings_fn:
                    query_embedding = embeddings_fn([query])[0]
                    
                    results = self._vector_store.query(
                        query_embeddings=[query_embedding],
                        n_results=min(self.config.max_context_docs, 10),
                        include=["documents", "metadatas"]
                    )
                    
                    # Map back to ClinicalDocument
                    retrieved = []
                    if results['metadatas'] and results['metadatas'][0]:
                        for meta in results['metadatas'][0]:
                            # Find matching document
                            for doc in self.knowledge_base.documents:
                                if doc.id == meta.get('id'):
                                    retrieved.append(doc)
                                    break
                    
                    return retrieved[:self.config.max_context_docs]
                    
            except Exception as e:
                print(f"Vector search failed, using keyword search: {e}")
        
        # Fallback to keyword search
        return self.knowledge_base.search(query)[:self.config.max_context_docs]
    
    def _build_context(self, retrieved_docs: List[ClinicalDocument]) -> str:
        """Build context string from retrieved documents."""
        if not retrieved_docs:
            return ""
        
        context_parts = []
        for doc in retrieved_docs:
            context_parts.append(f"### {doc.title}\n{doc.content}")
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, analysis_input: GaitAnalysisInput, context: str) -> str:
        """Build the prompt for the LLM."""
        
        # Patient summary
        patient_info = f"""
Patient: {analysis_input.patient_id}
"""
        if analysis_input.age:
            patient_info += f"Alter: {analysis_input.age} Jahre\n"
        if analysis_input.gender:
            patient_info += f"Geschlecht: {analysis_input.gender}\n"
        if analysis_input.height and analysis_input.weight:
            bmi = analysis_input.weight / ((analysis_input.height/100) ** 2)
            patient_info += f"Größe: {analysis_input.height} cm, Gewicht: {analysis_input.weight} kg (BMI: {bmi:.1f})\n"
        
        # Chief complaint
        if analysis_input.chief_complaint:
            patient_info += f"\nHauptbeschwerde: {analysis_input.chief_complaint}\n"
        
        if analysis_input.pain_location:
            patient_info += f"Schmerzlokalisation: {', '.join(analysis_input.pain_location)}\n"
        
        if analysis_input.pain_intensity is not None:
            patient_info += f"Schmerzintensität: {analysis_input.pain_intensity}/10\n"
        
        # Gait metrics summary
        metrics_info = ""
        if analysis_input.gait_metrics:
            m = analysis_input.gait_metrics
            metrics_info = f"""
Ganganalyse-Ergebnisse:
- Schritte: {m.get('step_count', 'N/A')}
- Cadenz: {m.get('cadence', 'N/A')} Schritte/min
- Symmetrie-Index: {m.get('symmetry_index', 'N/A')}%
- Schrittlänge links: {m.get('step_length_left', 'N/A')} cm
- Schrittlänge rechts: {m.get('step_length_right', 'N/A')} cm
- Swing Phase links: {m.get('swing_phase_left', 'N/A')}%
- Swing Phase rechts: {m.get('swing_phase_right', 'N/A')}%
- Doppelstandphase: {m.get('double_support_percent', 'N/A')}%
- Maximale Knieflexion: {m.get('max_knee_flexion', 'N/A')}°
"""
        
        prompt = f"""
Du bist ein erfahrener Physiotherapeut und Bewegungswissenschaftler, spezialisiert auf instrumentelle Ganganalyse.

Erstelle einen professionellen, klinischen Befundbericht basierend auf den folgenden Patientendaten und Ganganalyse-Ergebnissen.

{patient_info}
{metrics_info}

Verwende das folgende klinische Wissen als Referenz für deine Bewertung:

{context}

Erstelle einen strukturierten Befundbericht mit folgenden Abschnitten:

1. ZUSAMMENFASSUNG
   - Kurze Übersicht der wichtigsten Befunde
   - Gesamtbewertung des Gangbildes

2. BEWERTUNG DER GANGPARAMETER
   - Temporale Parameter (Cadenz, Schrittzeit, Phasen)
   - Räumliche Parameter (Schrittlänge, Symmetrie)
   - Kinematische Parameter (Gelenkwinkel)

3. AUFFÄLLIGKEITEN
   - Liste aller pathologischen Befunde
   - Einordnung nach klinischer Relevanz

4. VERDACHTSDIAGNOSEN / DIFFERENTIALDIAGNOSEN
   - Mögliche Ursachen der Gangstörung
   - Differentialdiagnostische Überlegungen

5. EMPFEHLUNGEN
   - Weiterführende Diagnostik
   - Therapeutische Maßnahmen
   - Ggf. Hilfsmittelversorgung

Antworte in professionellem klinischem Deutsch. Verwende Fachbegriffe wo angemessen, aber bleibe verständlich.
"""
        
        return prompt
    
    def generate_report(self, analysis_input: GaitAnalysisInput) -> str:
        """
        Generate a clinical gait analysis report.
        
        Args:
            analysis_input: Patient and gait analysis data
        
        Returns:
            Generated clinical report as text
        """
        provider = self._get_provider()
        
        # Build search query from patient data
        search_terms = []
        if analysis_input.chief_complaint:
            search_terms.append(analysis_input.chief_complaint.lower())
        if analysis_input.pain_location:
            search_terms.extend(analysis_input.pain_location)
        
        # Add metrics-based search terms
        if analysis_input.gait_metrics:
            m = analysis_input.gait_metrics
            if m.get('symmetry_index', 0) > 10:
                search_terms.append("asymmetrie")
            if m.get('cadence', 110) < 90:
                search_terms.append("niedrige cadenz")
            elif m.get('cadence', 110) > 130:
                search_terms.append("erhöhte cadenz")
            if m.get('max_knee_flexion', 65) < 50:
                search_terms.append("knieflexion")
        
        search_query = " ".join(search_terms) if search_terms else "ganganalyse normwerte"
        
        # Retrieve relevant context
        retrieved_docs = self._retrieve_context(search_query)
        context = self._build_context(retrieved_docs)
        
        # Build prompt
        prompt = self._build_prompt(analysis_input, context)
        
        # System prompt
        system_prompt = """
Du bist ein erfahrener klinischer Spezialist für Ganganalyse.
Erstelle professionelle, evidenzbasierte Befundberichte.
Verwende korrekte medizinische Fachterminologie.
Bleibe objektiv und vermeide Übertreibungen.
"""
        
        # Generate report
        report = provider.generate(prompt, system=system_prompt)
        
        return report
    
    def generate_structured_report(self, analysis_input: GaitAnalysisInput) -> Dict:
        """
        Generate a structured clinical report (JSON format).
        
        Args:
            analysis_input: Patient and gait analysis data
        
        Returns:
            Structured report as dictionary
        """
        provider = self._get_provider()
        
        # Retrieve context
        search_query = f"ganganalyse {' '.join(str(v) for v in analysis_input.gait_metrics.values() if v) if analysis_input.gait_metrics else ''}"
        retrieved_docs = self._retrieve_context(search_query)
        context = self._build_context(retrieved_docs)
        
        # Build prompt
        prompt = self._build_prompt(analysis_input, context)
        
        # Schema for structured output
        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "temporal_assessment": {"type": "string"},
                "spatial_assessment": {"type": "string"},
                "kinematic_assessment": {"type": "string"},
                "abnormalities": {"type": "array", "items": {"type": "string"}},
                "differential_diagnoses": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "array", "items": {"type": "string"}},
                "severity": {"type": "string", "enum": ["normal", "mild", "moderate", "severe"]}
            },
            "required": ["summary", "abnormalities", "recommendations", "severity"]
        }
        
        system_prompt = """
Du bist ein erfahrener klinischer Spezialist für Ganganalyse.
Antworte AUSSCHLIESSLICH mit validem JSON im angegebenen Schema.
Kein Markdown, kein zusätzlicher Text.
"""
        
        report = provider.generate_structured(prompt, schema, system=system_prompt)
        
        return report
    
    def set_provider(self, provider_name: str, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Change the LLM provider.
        
        Args:
            provider_name: Name of provider (openai, qwen, anthropic)
            api_key: API key (optional, uses env var if not provided)
            model: Model name (optional)
        """
        self.config.provider = provider_name
        if api_key:
            self.config.api_key = api_key
        if model:
            self.config.model = model
        
        # Reset provider to force recreation
        self._provider = None


# Convenience function for quick report generation
def quick_report(
    patient_id: str,
    gait_metrics: Dict,
    provider: str = "openai",
    api_key: Optional[str] = None
) -> str:
    """
    Quick report generation with minimal setup.
    
    Args:
        patient_id: Patient identifier
        gait_metrics: Dictionary of gait metrics
        provider: LLM provider name
        api_key: API key (optional)
    
    Returns:
        Generated report text
    """
    config = RAGConfig(provider=provider, api_key=api_key)
    engine = RAGEngine(config)
    
    analysis_input = GaitAnalysisInput(
        patient_id=patient_id,
        gait_metrics=gait_metrics
    )
    
    return engine.generate_report(analysis_input)
