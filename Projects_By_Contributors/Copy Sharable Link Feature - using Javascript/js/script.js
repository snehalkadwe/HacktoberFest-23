document.addEventListener('DOMContentLoaded', function () {
	const sharableLinkInput = document.getElementById('sharableLink');
	const copyButton = document.getElementById('copyButton');

	copyButton.addEventListener('click', function () {
		sharableLinkInput.select();
		document.execCommand('copy');
		alert('Link copied to clipboard!');
	});
});
