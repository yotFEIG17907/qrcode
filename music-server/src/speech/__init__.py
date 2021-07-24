import logging
import subprocess

logger = logging.getLogger("text.to.speech")


def do_text_to_speech(text: str) -> None:
    """
    Invoke a subprocess to cause flite to speak the text. This requires flite to have
    been installed. This blocks until the speech has finished
    :param text: Should be a short English phrase to be spoken
    :return: None
    """
    cmd = 'flite -voice slt ' + f"\"{text}\""
    try:
        subprocess.call(cmd, shell=True)
    except Exception as e:
        logger.error("Problem speechifying %s", str(e))
