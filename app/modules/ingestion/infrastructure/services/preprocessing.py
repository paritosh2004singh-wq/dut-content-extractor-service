from typing import List
from ...domain.models.document import PageImage
from ...domain.interfaces.capabilities import ImagePreprocessor

class PassThroughPreprocessor(ImagePreprocessor):
    def preprocess(self, image: PageImage) -> PageImage:
        image = self.deskew(image)
        image = self.correct_orientation(image)
        image = self.denoise(image)
        image = self.enhance_contrast(image)
        image = self.apply_threshold(image)
        image = self.normalize(image)
        return image

    def deskew(self, image: PageImage) -> PageImage:
        return image

    def correct_orientation(self, image: PageImage) -> PageImage:
        return image

    def denoise(self, image: PageImage) -> PageImage:
        return image

    def enhance_contrast(self, image: PageImage) -> PageImage:
        return image

    def apply_threshold(self, image: PageImage) -> PageImage:
        return image

    def normalize(self, image: PageImage) -> PageImage:
        return image
