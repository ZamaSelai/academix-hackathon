# verifier.py - AI Engine for AcademiX

from sentence_transformers import SentenceTransformer, util
import numpy as np

class EssayVerifier:
    def __init__(self):
        print("🔍 Loading AI model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Sample "cached" essays for comparison
        self.cached_essays = [
            "The industrial revolution began in Britain in the 18th century",
            "Photosynthesis converts light energy into chemical energy",
            "The water cycle involves evaporation, condensation, and precipitation",
            "DNA contains genetic information that determines traits",
            "The Roman Empire was one of the largest empires in history"
        ]
        
        self.cached_embeddings = self.model.encode(self.cached_essays)
        print("✅ AI model ready!")
    
    def get_originality_score(self, text):
        """Returns a score 0-100 showing how original the essay is"""
        if not text or len(text.strip()) < 10:
            return 0
        
        # NEW: Check for published source markers FIRST
        if self.check_against_known_sources(text):
            return 0  # ZERO for published content - no money!
        
        cleaned_text = self._clean_text(text)
        new_embedding = self.model.encode([cleaned_text])[0]
        similarities = util.cos_sim(new_embedding, self.cached_embeddings)[0]
        max_similarity = float(max(similarities))
        
        # CONVERT: Higher similarity = less original
        originality_score = max(0, (1 - max_similarity) * 100)
        
        # If similarity is very high, force score down
        if max_similarity > 0.85:
            return 0  # Too similar to cached content
        
        return min(100, originality_score)
    
    def get_similarity_score(self, text):
        """Returns the raw similarity percentage (0-100)"""
        if not text or len(text.strip()) < 10:
            return 0
        
        cleaned_text = self._clean_text(text)
        new_embedding = self.model.encode([cleaned_text])[0]
        similarities = util.cos_sim(new_embedding, self.cached_embeddings)[0]
        max_similarity = float(max(similarities))
        return max_similarity * 100  # Return as percentage
    
    def check_academic_tone(self, text):
        """Checks if the text sounds academic"""
        academic_words = [
            'research', 'study', 'analysis', 'data', 'results',
            'conclusion', 'methodology', 'evidence', 'findings',
            'hypothesis', 'theory', 'experiment', 'observation',
            'therefore', 'however', 'furthermore', 'consequently',
            'according', 'demonstrate', 'suggest', 'indicate'
        ]
        
        text_lower = text.lower()
        found = sum(1 for word in academic_words if word in text_lower)
        
        # Make scoring more generous
        score = min(100, (found / len(academic_words)) * 150)
        return min(100, score)
    
    def check_against_known_sources(self, text):
        """NEW: Check if text contains markers of published academic work"""
        
        # Expanded list of publisher markers
        publisher_markers = [
            # Academic publishers
            "globethics.net", "doi.org", "creativecommons.org",
            "ISBN", "All rights reserved", "Springer", "Elsevier",
            "Taylor & Francis", "Sage Publications", "Cambridge University Press",
            "Oxford University Press", "Wiley", "IEEE", "ACM", "UNESCO",
            "International Committee of the Red Cross", "ICRC",
            "World Health Organization", "WHO", "United Nations",
            "World Bank", "IMF", "International Labour Organization",
            "ILO", "UNICEF", "UNHCR", "WIPO", "ITU",
            
            # Academic paper markers
            "This page was generated automatically", "Download date",
            "Item License", "Attribution-NonCommercial-NoDerivatives",
            "Globethics.net Global Series", "Series Editors",
            "Managing Editor", "Assistant Editor",
            "All web links in this text have been verified",
            "published", "©", "Copyright", "permission",
            
            # Academic journal markers
            "Abstract", "Introduction", "Methodology", "Conclusion",
            "References", "Bibliography", "Appendix", "Keywords",
            "DOI", "ISSN", "Volume", "Issue"
        ]
        
        text_lower = text.lower()
        found = sum(1 for marker in publisher_markers if marker.lower() in text_lower)
        
        # If 2+ markers found, it's likely published content
        return found >= 2
    
    def _clean_text(self, text):
        """Simple text cleaning"""
        text = text.lower()
        text = ' '.join(text.split())
        return text
    
    def count_words(self, text):
        """Count words in essay"""
        return len(text.split())